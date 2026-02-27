# image_comparator.py
import os
from PIL import Image
import imagehash
from collections import defaultdict

def find_similar_images(folder_path, hash_size=8, similarity_threshold=5, progress_callback=None):
    """
    Finds similar images in a given folder using perceptual hashing (pHash) 
    and groups them based on similarity.

    Args:
        folder_path (str): The path to the folder containing images.
        hash_size (int): The size of the hash (higher means more detail, slower).
        similarity_threshold (int): Maximum Hamming distance for images to be considered similar.
        progress_callback (function, optional): A function to call for progress updates.
                                                It receives (current_step, total_steps, message).

    Returns:
        dict: A dictionary where keys are representative image paths and
              values are lists of similar image paths (including the key).
              Returns None if the folder is invalid.
              Returns an empty dict if no images are found or no similarities detected.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at {folder_path}")
        if progress_callback:
            progress_callback(0, 1, f"Erro: Pasta não encontrada em {folder_path}")
        return None

    image_files = []
    supported_formats = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")
    try:
        all_files = os.listdir(folder_path)
    except OSError as e:
        print(f"Error listing directory {folder_path}: {e}")
        if progress_callback:
            progress_callback(0, 1, f"Erro ao listar diretório: {e}")
        return None

    for filename in all_files:
        if filename.lower().endswith(supported_formats):
            image_files.append(os.path.join(folder_path, filename))

    if not image_files:
        print("No supported image files found in the folder.")
        if progress_callback:
            progress_callback(1, 1, "Nenhum arquivo de imagem suportado encontrado.")
        return {}

    total_images = len(image_files)
    hashes = {}
    print(f"Processing {total_images} images to calculate hashes...")
    if progress_callback:
        progress_callback(0, total_images * 2, f"Calculando hashes para {total_images} imagens...") # Initial step

    processed_count = 0
    for img_path in image_files:
        try:
            with Image.open(img_path) as img:
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                hash_val = imagehash.phash(img, hash_size=hash_size)
                hashes[img_path] = hash_val
        except Exception as e:
            print(f"Could not process image {img_path}: {e}")
            # Optionally inform user about skipped files via callback
        finally:
            processed_count += 1
            if progress_callback:
                # Progress for hashing phase (0 to total_images)
                progress_callback(processed_count, total_images * 2, f"Calculando hash: {processed_count}/{total_images}")

    if not hashes:
        print("No image hashes were generated (all images failed to process?).")
        if progress_callback:
            progress_callback(total_images * 2, total_images * 2, "Nenhuma imagem pôde ser processada.")
        return {}

    # --- Revised Grouping Logic using Connected Components --- 
    print("Comparing hashes to build similarity graph...")
    img_paths = list(hashes.keys()) # Only compare images that were successfully hashed
    adj = defaultdict(list) # Adjacency list for the graph
    num_hashed_images = len(img_paths)
    total_comparisons_possible = num_hashed_images * (num_hashed_images - 1) // 2
    comparison_count = 0
    # Total steps = hashing steps + comparison steps
    total_steps_overall = total_images + total_comparisons_possible 

    # Step 1: Build the graph based on similarity threshold
    for i in range(num_hashed_images):
        # Update progress during comparison phase (total_images to total_steps_overall)
        current_progress_step = total_images + comparison_count 
        progress_message = f"Comparando pares: {comparison_count}/{total_comparisons_possible}"
        if progress_callback:
            progress_callback(current_progress_step, total_steps_overall, progress_message)
            
        for j in range(i + 1, num_hashed_images):
            # Hashes dictionary only contains valid keys now
            distance = hashes[img_paths[i]] - hashes[img_paths[j]]
            if distance <= similarity_threshold:
                adj[img_paths[i]].append(img_paths[j])
                adj[img_paths[j]].append(img_paths[i])
            comparison_count += 1 # Increment comparison counter

    print("Finding connected components (groups)...")
    # Step 2: Find connected components (groups) using BFS
    visited = set()
    similar_groups_final = {}

    for img_path in img_paths: # Iterate through successfully hashed images
        if img_path not in visited and img_path in adj: # Start traversal if part of a similarity edge and not visited
            current_group = []
            q = [img_path] # Queue for BFS
            visited.add(img_path)

            while q:
                u = q.pop(0)
                current_group.append(u)
                # Check neighbors in the adjacency list
                if u in adj:
                    for v in adj[u]:
                        if v not in visited:
                            visited.add(v)
                            q.append(v)
            
            # Only store groups with more than one image
            if len(current_group) > 1:
                representative = min(current_group) # Use lexicographically smallest path as key
                similar_groups_final[representative] = sorted(current_group)
        
        elif img_path not in visited:
             # Mark images with no similarities as visited so we don't re-check
             visited.add(img_path)

    final_message = f"Concluído. Encontrados {len(similar_groups_final)} grupos de imagens similares."
    print(final_message)
    if progress_callback:
        # Ensure progress reaches 100%
        progress_callback(total_steps_overall, total_steps_overall, final_message)

    return similar_groups_final

# Example usage (for testing the module directly)
if __name__ == '__main__':
    test_folder = "test_images_comparator"
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)
        try:
            print(f"Creating dummy images in '{test_folder}'...")
            Image.new('RGB', (100, 50), color = 'red').save(os.path.join(test_folder, 'red1.png'))
            Image.new('RGB', (100, 50), color = 'red').save(os.path.join(test_folder, 'red2.jpg'))
            Image.new('RGB', (100, 50), color = 'blue').save(os.path.join(test_folder, 'blue1.png'))
            img_red_slight = Image.new('RGB', (100, 50), color = (254, 0, 0))
            img_red_slight.save(os.path.join(test_folder, 'red_similar.png'))
            img_red_rotated = Image.new('RGB', (50, 100), color = 'red') # Rotated
            img_red_rotated.save(os.path.join(test_folder, 'red_rotated.png'))
            Image.new('RGB', (80, 80), color = 'green').save(os.path.join(test_folder, 'green.png'))
            with open(os.path.join(test_folder, 'not_an_image.txt'), 'w') as f:
                f.write("hello")
            print("Dummy test images created.")
        except Exception as e:
            print(f"Could not create dummy images: {e}")

    print(f"\nRunning similarity check on folder: {test_folder}")
    def simple_progress(current, total, message):
        percent = int((current/total * 100)) if total > 0 else 0
        print(f"Progress: {percent}% ({current}/{total}) - {message}")

    # Test with threshold 5
    print("\n--- Test with Threshold 5 ---")
    similar_found_5 = find_similar_images(test_folder, similarity_threshold=5, progress_callback=simple_progress)
    if similar_found_5:
        print("\nSimilar image groups found (Threshold=5):")
        group_num = 1
        for representative, group in similar_found_5.items():
            print(f"\n--- Grupo {group_num} --- (Representante: {os.path.basename(representative)})")
            for img_path in group:
                print(f"  - {os.path.basename(img_path)}")
            group_num += 1
    else:
        print("\nNo similar images found with threshold 5.")

    # Test with threshold 0 (exact duplicates)
    print("\n--- Test with Threshold 0 ---")
    similar_found_0 = find_similar_images(test_folder, similarity_threshold=0, progress_callback=simple_progress)
    if similar_found_0:
        print("\nSimilar image groups found (Threshold=0):")
        group_num = 1
        for representative, group in similar_found_0.items():
            print(f"\n--- Grupo {group_num} --- (Representante: {os.path.basename(representative)})")
            for img_path in group:
                print(f"  - {os.path.basename(img_path)}")
            group_num += 1
    else:
        print("\nNo similar images found with threshold 0.")


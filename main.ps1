Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Função para encontrar arquivos duplicados
function Find-DuplicateFiles {
    param([string]$FolderPath)
    
    Write-Host "Procurando arquivos duplicados em: $FolderPath"
    
    # Obter todos os arquivos da pasta e subpastas
    $allFiles = Get-ChildItem -Path $FolderPath -File -Recurse -ErrorAction SilentlyContinue
    
    # Agrupar arquivos por nome (sem considerar o caminho)
    $groupedFiles = $allFiles | Group-Object -Property Name | Where-Object { $_.Count -gt 1 }
    
    $duplicateFiles = @()
    foreach ($group in $groupedFiles) {
        foreach ($file in $group.Group) {
            $duplicateFiles += [PSCustomObject]@{
                Nome = $file.Name
                CaminhoCompleto = $file.FullName
                Tamanho = [math]::Round($file.Length / 1KB, 2)
                DataModificacao = $file.LastWriteTime
                Selecionado = $false
            }
        }
    }
    
    return $duplicateFiles
}

# Função para excluir arquivos selecionados
function Remove-SelectedFiles {
    param([array]$FilesToDelete)
    
    $deletedCount = 0
    $errorCount = 0
    
    foreach ($file in $FilesToDelete) {
        try {
            if (Test-Path $file.CaminhoCompleto) {
                Remove-Item -Path $file.CaminhoCompleto -Force
                $deletedCount++
                Write-Host "Excluído: $($file.CaminhoCompleto)"
            }
        }
        catch {
            $errorCount++
            Write-Host "Erro ao excluir: $($file.CaminhoCompleto) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    return @{
        Deletados = $deletedCount
        Erros = $errorCount
    }
}

# Criar formulário principal
$form = New-Object System.Windows.Forms.Form
$form.Text = "Localizador de Arquivos Duplicados"
$form.Size = New-Object System.Drawing.Size(800, 600)
$form.StartPosition = "CenterScreen"
$form.MinimumSize = New-Object System.Drawing.Size(600, 400)

# Painel superior para seleção de pasta
$topPanel = New-Object System.Windows.Forms.Panel
$topPanel.Height = 60
$topPanel.Dock = "Top"

# Label para pasta
$lblPasta = New-Object System.Windows.Forms.Label
$lblPasta.Text = "Pasta:"
$lblPasta.Location = New-Object System.Drawing.Point(10, 15)
$lblPasta.Size = New-Object System.Drawing.Size(50, 20)
$topPanel.Controls.Add($lblPasta)

# TextBox para exibir caminho da pasta
$txtPasta = New-Object System.Windows.Forms.TextBox
$txtPasta.Location = New-Object System.Drawing.Point(65, 12)
$txtPasta.Size = New-Object System.Drawing.Size(500, 20)
$txtPasta.ReadOnly = $true
$topPanel.Controls.Add($txtPasta)

# Botão para selecionar pasta
$btnSelecionarPasta = New-Object System.Windows.Forms.Button
$btnSelecionarPasta.Text = "Selecionar Pasta"
$btnSelecionarPasta.Location = New-Object System.Drawing.Point(575, 10)
$btnSelecionarPasta.Size = New-Object System.Drawing.Size(100, 25)
$topPanel.Controls.Add($btnSelecionarPasta)

# Botão para buscar duplicados
$btnBuscar = New-Object System.Windows.Forms.Button
$btnBuscar.Text = "Buscar Duplicados"
$btnBuscar.Location = New-Object System.Drawing.Point(685, 10)
$btnBuscar.Size = New-Object System.Drawing.Size(100, 25)
$btnBuscar.Enabled = $false
$topPanel.Controls.Add($btnBuscar)

# Painel para controles da lista
$controlPanel = New-Object System.Windows.Forms.Panel
$controlPanel.Height = 40
$controlPanel.Dock = "Top"

# Checkbox para selecionar todos
$chkSelecionarTodos = New-Object System.Windows.Forms.CheckBox
$chkSelecionarTodos.Text = "Selecionar Todos"
$chkSelecionarTodos.Location = New-Object System.Drawing.Point(10, 10)
$chkSelecionarTodos.Size = New-Object System.Drawing.Size(120, 20)
$controlPanel.Controls.Add($chkSelecionarTodos)

# Botão para excluir selecionados
$btnExcluir = New-Object System.Windows.Forms.Button
$btnExcluir.Text = "Excluir Selecionados"
$btnExcluir.Location = New-Object System.Drawing.Point(140, 8)
$btnExcluir.Size = New-Object System.Drawing.Size(120, 25)
$btnExcluir.Enabled = $false
$btnExcluir.BackColor = [System.Drawing.Color]::LightCoral
$controlPanel.Controls.Add($btnExcluir)

# Label para status
$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Text = "Selecione uma pasta para começar"
$lblStatus.Location = New-Object System.Drawing.Point(280, 12)
$lblStatus.Size = New-Object System.Drawing.Size(300, 20)
$controlPanel.Controls.Add($lblStatus)

# DataGridView para exibir arquivos duplicados
$dgvArquivos = New-Object System.Windows.Forms.DataGridView
$dgvArquivos.AllowUserToAddRows = $false
$dgvArquivos.AllowUserToDeleteRows = $false
$dgvArquivos.SelectionMode = "FullRowSelect"
$dgvArquivos.MultiSelect = $true
$dgvArquivos.AutoSizeColumnsMode = "Fill"
$dgvArquivos.ScrollBars = "Both"
$dgvArquivos.AutoSizeRowsMode = "None"
$dgvArquivos.RowHeadersVisible = $true
$dgvArquivos.RowHeadersWidth = 25
$dgvArquivos.AllowUserToResizeColumns = $true
$dgvArquivos.AllowUserToResizeRows = $false
$dgvArquivos.ColumnHeadersHeightSizeMode = "DisableResizing"
$dgvArquivos.ColumnHeadersHeight = 25
$dgvArquivos.MaximumSize = New-Object System.Drawing.Size(1150, 700)
$dgvArquivos.DefaultCellStyle.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$dgvArquivos.ColumnHeadersDefaultCellStyle.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$dgvArquivos.BackgroundColor = [System.Drawing.Color]::White
$dgvArquivos.GridColor = [System.Drawing.Color]::LightGray
$dgvArquivos.Dock = "Fill"

# Adicionar controles ao formulário na ordem correta
$form.Controls.Add($dgvArquivos)  # Adicionar primeiro (vai para o fundo)
$form.Controls.Add($controlPanel) # Adicionar segundo (vai para cima do DataGridView)
$form.Controls.Add($topPanel)     # Adicionar por último (vai para o topo)

# Configurar colunas do DataGridView
$dgvArquivos.Columns.Add("Selecionado", "Selecionar")
$dgvArquivos.Columns["Selecionado"].Width = 80
$dgvArquivos.Columns["Selecionado"].DefaultCellStyle.Alignment = "MiddleCenter"

$dgvArquivos.Columns.Add("Nome", "Nome do Arquivo")
$dgvArquivos.Columns.Add("CaminhoCompleto", "Caminho Completo")
$dgvArquivos.Columns.Add("Tamanho", "Tamanho (KB)")
$dgvArquivos.Columns["Tamanho"].Width = 100
$dgvArquivos.Columns["Tamanho"].DefaultCellStyle.Alignment = "MiddleRight"

$dgvArquivos.Columns.Add("DataModificacao", "Data de Modificação")
$dgvArquivos.Columns["DataModificacao"].Width = 150

# Variável global para armazenar arquivos duplicados
$global:duplicateFiles = @()

# Event handler para seleção de pasta
$btnSelecionarPasta.Add_Click({
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = "Selecione a pasta para buscar arquivos duplicados"
    
    if ($folderBrowser.ShowDialog() -eq "OK") {
        $txtPasta.Text = $folderBrowser.SelectedPath
        $btnBuscar.Enabled = $true
        $lblStatus.Text = "Pasta selecionada. Clique em 'Buscar Duplicados' para continuar."
    }
})

# Event handler para buscar duplicados
$btnBuscar.Add_Click({
    if (-not (Test-Path $txtPasta.Text)) {
        [System.Windows.Forms.MessageBox]::Show("Pasta não encontrada!", "Erro", "OK", "Error")
        return
    }
    
    $lblStatus.Text = "Buscando arquivos duplicados..."
    $form.Cursor = [System.Windows.Forms.Cursors]::WaitCursor
    
    # Limpar grid
    $dgvArquivos.Rows.Clear()
    
    try {
        $global:duplicateFiles = Find-DuplicateFiles -FolderPath $txtPasta.Text
        
        if ($global:duplicateFiles.Count -eq 0) {
            $lblStatus.Text = "Nenhum arquivo duplicado encontrado."
            $btnExcluir.Enabled = $false
        }
        else {
            # Adicionar arquivos ao grid
            foreach ($file in $global:duplicateFiles) {
                $row = $dgvArquivos.Rows.Add()
                $dgvArquivos.Rows[$row].Cells["Selecionado"].Value = $false
                $dgvArquivos.Rows[$row].Cells["Nome"].Value = $file.Nome
                $dgvArquivos.Rows[$row].Cells["CaminhoCompleto"].Value = $file.CaminhoCompleto
                $dgvArquivos.Rows[$row].Cells["Tamanho"].Value = $file.Tamanho
                $dgvArquivos.Rows[$row].Cells["DataModificacao"].Value = $file.DataModificacao.ToString("dd/MM/yyyy HH:mm:ss")
            }
            
            $lblStatus.Text = "$($global:duplicateFiles.Count) arquivos duplicados encontrados."
            $btnExcluir.Enabled = $true
        }
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Erro ao buscar arquivos: $($_.Exception.Message)", "Erro", "OK", "Error")
        $lblStatus.Text = "Erro ao buscar arquivos."
    }
    finally {
        $form.Cursor = [System.Windows.Forms.Cursors]::Default
    }
})

# Event handler para selecionar todos
$chkSelecionarTodos.Add_CheckedChanged({
    foreach ($row in $dgvArquivos.Rows) {
        $row.Cells["Selecionado"].Value = $chkSelecionarTodos.Checked
    }
})

# Event handler para clique nas células (checkbox)
$dgvArquivos.Add_CellClick({
    param($sender, $e)
    
    if ($e.ColumnIndex -eq 0 -and $e.RowIndex -ge 0) {  # Coluna checkbox
        $currentValue = $dgvArquivos.Rows[$e.RowIndex].Cells["Selecionado"].Value
        $dgvArquivos.Rows[$e.RowIndex].Cells["Selecionado"].Value = -not $currentValue
    }
})

# Event handler para excluir arquivos selecionados
$btnExcluir.Add_Click({
    $selectedFiles = @()
    
    foreach ($row in $dgvArquivos.Rows) {
        if ($row.Cells["Selecionado"].Value -eq $true) {
            $filePath = $row.Cells["CaminhoCompleto"].Value
            $selectedFile = $global:duplicateFiles | Where-Object { $_.CaminhoCompleto -eq $filePath }
            if ($selectedFile) {
                $selectedFiles += $selectedFile
            }
        }
    }
    
    if ($selectedFiles.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show("Nenhum arquivo selecionado para exclusão.", "Aviso", "OK", "Warning")
        return
    }
    
    $confirmResult = [System.Windows.Forms.MessageBox]::Show(
        "Tem certeza que deseja excluir $($selectedFiles.Count) arquivo(s) selecionado(s)?`n`nEsta ação não pode ser desfeita!",
        "Confirmar Exclusão",
        "YesNo",
        "Warning"
    )
    
    if ($confirmResult -eq "Yes") {
        $lblStatus.Text = "Excluindo arquivos selecionados..."
        $form.Cursor = [System.Windows.Forms.Cursors]::WaitCursor
        
        try {
            $result = Remove-SelectedFiles -FilesToDelete $selectedFiles
            
            # Remover linhas dos arquivos excluídos do grid
            $rowsToRemove = @()
            foreach ($row in $dgvArquivos.Rows) {
                if ($row.Cells["Selecionado"].Value -eq $true) {
                    $filePath = $row.Cells["CaminhoCompleto"].Value
                    if (-not (Test-Path $filePath)) {
                        $rowsToRemove += $row
                    }
                }
            }
            
            foreach ($row in $rowsToRemove) {
                $dgvArquivos.Rows.Remove($row)
            }
            
            $lblStatus.Text = "Exclusão concluída. $($result.Deletados) arquivo(s) excluído(s), $($result.Erros) erro(s)."
            
            if ($result.Erros -gt 0) {
                [System.Windows.Forms.MessageBox]::Show(
                    "Alguns arquivos não puderam ser excluídos. Verifique o console para mais detalhes.",
                    "Aviso",
                    "OK",
                    "Warning"
                )
            }
        }
        catch {
            [System.Windows.Forms.MessageBox]::Show("Erro durante a exclusão: $($_.Exception.Message)", "Erro", "OK", "Error")
            $lblStatus.Text = "Erro durante a exclusão."
        }
        finally {
            $form.Cursor = [System.Windows.Forms.Cursors]::Default
        }
    }
})

# Exibir o formulário
Write-Host "Iniciando aplicação de localização de arquivos duplicados..."
$form.ShowDialog() | Out-Null 
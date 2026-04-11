$path = "C:\Users\PC\Documents\AI Sales OS\AI_Sales_OS_Analysis_Report_Branded.docx"
$dest = "C:\Users\PC\Documents\AI Sales OS\docx_unpack"
Expand-Archive -LiteralPath $path -DestinationPath $dest -Force
Write-Host "Unpacked to: $dest"

$response = Invoke-RestMethod -Uri "https://api.github.com/repos/RahulARanger/CO-PO-Mapping/releases/latest" -Method "GET"
    
$download_url = $response.assets.browser_download_url;
Write-Output $download_url
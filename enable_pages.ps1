$response = gh api --method PUT repos/hemateja566/portfolio-static/pages -f source.branch=master -f build_type=none
Write-Host "GitHub Pages enabled successfully"
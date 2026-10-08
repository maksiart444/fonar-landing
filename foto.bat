@echo off
cd /d "%~dp0"
if not exist "static\img" mkdir "static\img"
echo Downloading photos...
set B=https://dropt.in.ua/image/cache/catalog/products/56/56994_
powershell -NoProfile -Command "$b='%B%'; $f=@{'main.png'='123e36e3780b';'photo1.png'='229cfa5ed47a';'photo2.png'='c45a1429d58f';'photo3.png'='eb195363973b'}; foreach($k in $f.Keys){ try { Invoke-WebRequest -UseBasicParsing -Uri ($b+$f[$k]+'-1000x1000.png') -OutFile ('static\img\'+$k); Write-Host ('OK  '+$k) } catch { Write-Host ('ERR '+$k) } }"
echo.
echo Done. Refresh the site in the browser (F5).
pause

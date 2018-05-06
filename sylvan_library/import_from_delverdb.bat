php C:\wamp\www\delverdb\dump.php cardchanges > cardchanges.txt
php C:\wamp\www\delverdb\dump.php usercards > usercards.txt

python manage.py import_usercards Liam usercards.txt
python manage.py import_usercardchanges Liam cardchanges.txt
web: gunicorn --worker-tmp-dir /dev/shm -k gevent -w 2 dashboard:app 
worker: python main.py 
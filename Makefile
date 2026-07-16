.PHONY: scrap up

scrap:
	sudo docker exec django_app python3 manage.py shell -c "from app.tasks import scrap_home_page; scrap_home_page.delay()"
	sudo docker logs celery_worker -f

up: 
	sudo docker-compose up -d --build
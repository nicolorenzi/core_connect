run:
	python main.py

tailwind:
	npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

dev:
	make tailwind & make run
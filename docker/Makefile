alpine:
	docker build -t runelite-alpine -f Dockerfile.alpine .

# 
run-alpine:
	docker run --rm -p 5800:5800 -p 5900:5900 --mount type=bind,source="$$(pwd)"/mnt/alpine,target=/config runelite-alpine
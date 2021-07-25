build-devel:
	docker image build -t genealogy-development .

build-devel-new:
	docker image rm -f genealogy-development
	docker image build -t genealogy-development .

start-devel:
	docker container run --rm -it -v $$(pwd):/home/appuser/app --name genealogy-development genealogy-development

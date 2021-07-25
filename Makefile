build-devel:
	docker image build -t genealogy-development .

build-devel-new:
	docker image rm -f genealogy-development
	docker image build -t genealogy-development .

start-devel:
	docker container run --rm -it -v $$(pwd):/home/appuser/app --name genealogy-development genealogy-development

test:
	./convert.py -d GED2CSV -g gedcom_static/genealogy_all_20210626.ged -p ./gedcom_output/p.csv -f ./gedcom_output/f.csv -v
	rm ./gedcom_output/p.csv ./gedcom_output/f.csv

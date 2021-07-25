build-devel:
	docker image build -t genealogy-development .

build-devel-new:
	docker image rm -f genealogy-development
	docker image build -t genealogy-development .

start-devel:
	docker container run --rm -it -v $$(pwd)/..:/home/appuser/app --name genealogy-development genealogy-development

test:
	./convert.py -d GED2CSV -g ../static/genealogy_all_20210626.ged -p ../output/test_p.csv -f ../output/test_f.csv -s ../output/test_s.csv -v

test-non-verbose:
	./convert.py -d GED2CSV -g ../static/genealogy_all_20210626.ged -p ../output/test_p.csv -f ../output/test_f.csv -s ../output/test_s.csv

clean:
	rm ../output/test_p.csv ../output/test_f.csv ../output/test_s.csv

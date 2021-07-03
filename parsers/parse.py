import pandas as pd

class GedcomParser:
    def __init__(self, gedcom_file, family_file, person_file):
        self.gedcom_file = gedcom_file
        self.family_file = family_file
        self.person_file = person_file

    def gedcom_to_csv(self):
        # open the file and read lines
		self.gedcom_lines = self.get_gedcom_lines()

        # find the first individual
		first_indi_index = self.find_first_indi_entry()
		first_fam_index = self.find_first_fam_entry()
		end_fam_index = self.find_end_fam_entry()

        # read all individual entries, build dict
		for i in range(first_indi_index, first_fam_index):
        # find the first family
        # read all family entries, build dict

    def csv_to_gedcom(self):
        pass

    def handle_tag(self):
        pass


	def get_gedcom_lines(self):
        with open(self.gedcom_file, "r") as f:
            lines = f.readlines()
		return lines

	def find_first_indi_entry(self):
		for i, line in enumerate(self.gedcom_lines):

	def find_first_fam_entry(self):

	def find_end_fam_entry(self):

import pandas as pd

def pipeline():
	
	df = pd.read_csv("iris.csv")

	df = df[df["species"] == "lotus"]

	df["col"] = "hello"

	df.to_csv("iris2.csv")

def pipeline2():

	df = pd.read_csv("iris2.csv")
	df2 = pd.read_csv("iris3.csv")

			

# EDA Exercise #1 for books.csv

# Import statement
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Read into Pandas
books = pd.read_csv("/Users/christine/Desktop/DataCamp Data/clean_books.csv")

# Look at head
books.head()

# Look at data features
books.info()

# Look at categorical columns
books.value_counts("genre")

# Description
books.describe()

# Visualize numerical data
sns.histplot(data = books, x = "rating")
plt.show()

# Set the bin-width:
sns.histplot(data=books, x="2021", binwidth=1)

# Data Validation 
books.info()


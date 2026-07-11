General processing for data manipulation of my frankly massive LEGO collection



Headers for 'Identified Lego Sets - python_export.csv' are as follows: 
Name,ID,Status,Retail Price,Current Price
e.g: A-wing Starfighter - UCS,75275,New,$199.99 ,$198.9984



credentials_file_bricklink contains, each item on a new line with no formatting: 
consumer\_key
consumer\_secret
token\_value
token\_secret

credentials_file_brickset contains, each item on a new line with no formatting: 
apiKey




pieces\_list\_by\_set stores a full list of every piece in each set locally, so may be quite large depending on the size of the collection (this file is around 2MB on my machine)


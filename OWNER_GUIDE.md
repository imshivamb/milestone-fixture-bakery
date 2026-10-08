# Crumb & Co website: owner guide

This guide is for the bakery owner. You do not need to write code to keep the site up to date.

## Updating the menu

The menu on the home page is built from the file `products.csv`. Each line is one product:
the product name, a comma, then the price without a currency sign, for example
`Sourdough loaf,6.50`. To add a product, add a new line at the end. To change a price, edit the
number on that product's line. To remove a product, delete its line. Keep the first line
(`name,price`) as it is.

## Making the change go live

Save the file, commit it and push it to the main branch. Then restart the site
(`python3 app.py`) or redeploy it on your host; the new menu appears as soon as the site starts
again. If a product does not appear, check that its line has exactly one comma.

## Getting help

Email the developer with a screenshot of the page and a copy of `products.csv`.

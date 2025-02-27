import pandas as pd
from typing import Dict, Union, List

class ProductPricing:
    def __init__(self, csv_path: str = "products.csv"):
        self.products_df = pd.read_csv(csv_path)
    
    def calculate_price(self, product_code: str, quantity: int) -> Dict[str, Union[float, str, int]]:
        """
        Calculate the total price for a given product and quantity
        
        Args:
            product_code: The product code to look up
            quantity: Number of units to calculate price for
            
        Returns:
            Dictionary containing price details
        """
        try:
            product = self.products_df[self.products_df['Product_Code'] == product_code].iloc[0]
            total_price = product['RRP'] * quantity
            
            return {
                "product_description": product['Description'],
                "unit_price": product['RRP'],
                "quantity": quantity,
                "total_price": total_price,
                "currency": "EUR"
            }
        except IndexError:
            raise ValueError(f"Product code {product_code} not found")
    
    def get_all_products(self) -> List[Dict[str, Union[str, float]]]:
        """Return list of all available products"""
        return self.products_df.to_dict('records') 
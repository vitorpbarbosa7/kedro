import pandas as pd

# auxiliar functions with underscore
# string for true
def _is_true(x):
    return x == "t"

# remove % from dataset
def _parse_percentage(x):
    x = x.str.replace("%", "")
    x = x.astype(float) / 100
    return x

# replace $ with nothing and , with nothing
def _parse_money(x):
    x = x.str.replace("$", "").str.replace(",", "")
    x = x.astype(float)
    return x

# if it is true, return "t" for iata_approved
# convert company rating to float
def preprocess_companies(companies: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the data for companies.

    Args:
        companies: Raw data.
    Returns:
        Preprocessed data, with `company_rating` converted to a float and
        `iata_approved` converted to boolean.
    """
    companies["iata_approved"] = _is_true(companies["iata_approved"])
    companies["company_rating"] = _parse_percentage(companies["company_rating"])

    # companies = companies.to_parquet()
    return companies

# if it is true return "t" for d_check_complete
# if it is true return "t" for moon_clearence_complete
# convert price to float
def preprocess_shuttles(shuttles: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the data for shuttles.

    Args:
        shuttles: Raw data.
    Returns:
        Preprocessed data, with `price` converted to a float and `d_check_complete`,
        `moon_clearance_complete` converted to boolean.
    """
    shuttles["d_check_complete"] = _is_true(shuttles["d_check_complete"])
    shuttles["moon_clearance_complete"] = _is_true(shuttles["moon_clearance_complete"])
    shuttles["price"] = _parse_money(shuttles["price"])
    return shuttles
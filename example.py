"""Example Python file to demonstrate the LLM docs hook."""

def calculate_fibonacci(n, memo=None):
    """Calculates the nth Fibonacci number using memoization.

    This function computes the Fibonacci number at position `n` using a recursive approach with memoization to optimize performance. It stores previously computed Fibonacci numbers in a dictionary to avoid redundant calculations.

    Args:
        n (int): The position in the Fibonacci sequence to calculate. Must be a non-negative integer.
        memo (dict, optional): A dictionary used to store previously computed Fibonacci numbers. Defaults to None.

    Returns:
        int: The Fibonacci number at position `n`.
    """
    if memo is None:
        memo = {}
    
    if n in memo:
        return memo[n]
    
    if n <= 1:
        return n
    
    memo[n] = calculate_fibonacci(n-1, memo) + calculate_fibonacci(n-2, memo)
    return memo[n]


class DataProcessor:
    """A class for processing data from a specified source.

        This class is responsible for loading, processing, and retrieving statistics 
        from the data. It allows for custom transformations to be applied to the 
        loaded data.

        Attributes:
            data_source (str): The source from which data is loaded.
            processed_data (list): A list of processed data after applying the 
                transformation function.

        Methods:
            load_data() -> list:
                Loads raw data from the data source.

            process_data(transformation_func: Callable[[Any], Any]) -> list:
                Processes the loaded data using the provided transformation function.

            get_statistics() -> dict:
                Computes and returns basic statistics (count, sum, mean) of the 
                processed data.
    """
    def __init__(self, data_source):
        """Initializes the DataProcessor with a specified data source.

        Args:
            data_source (str): The source from which to load data.

        Attributes:
            data_source (str): The source from which data will be loaded.
            processed_data (list): A list to store processed data.

        Loads data from the specified data source.

        Returns:
            list: A list of integers representing the loaded data.
        """
        self.data_source = data_source
        self.processed_data = []

    def load_data(self):
        """Processes raw data using a specified transformation function.

            This method loads raw data from the data source, applies the given transformation function to each item, 
            and stores the processed data in the instance variable `processed_data`.

            Args:
                transformation_func (Callable[[int], Any]): A function that takes an integer as input and returns 
                a transformed value. This function will be applied to each item in the loaded data.

            Returns:
                List[Any]: A list containing the transformed data after applying the transformation function 
                to each item in the raw data.
        """
        # Simulate loading data
        return list(range(100))

    def process_data(self, transformation_func):
        """Processes raw data using a transformation function and computes statistics.

            This method loads raw data, applies a specified transformation function to each item,
            and stores the processed data. It also provides a method to retrieve statistics about the
            processed data.

            Args:
                transformation_func (Callable[[int], Any]): A function that takes an integer as input
                    and returns a transformed value.

            Returns:
                List[Any]: A list of processed data after applying the transformation function.

            Raises:
                ValueError: If the transformation function is not callable.
        """
        raw_data = self.load_data()
        self.processed_data = [transformation_func(item) for item in raw_data]
        return self.processed_data

    def get_statistics(self):
        """Calculates statistics for the processed data.

            This method computes the count, sum, and mean of the processed data. 
            If the processed data is empty, it returns default values.

            Returns:
                dict: A dictionary containing the following keys:
                    - count (int): The number of items in the processed data.
                    - sum (float): The total sum of the processed data.
                    - mean (float): The mean value of the processed data. 
                                    Returns 0 if the count is 0.
        """
        if not self.processed_data:
            return {"count": 0, "sum": 0, "mean": 0}
        
        count = len(self.processed_data)
        total = sum(self.processed_data)
        mean = total / count
        
        return {
            "count": count,
            "sum": total,
            "mean": mean
        }


def complex_algorithm(input_data, threshold=0.5, normalize=True):
    """Processes a list of numerical input data by normalizing it and applying a transformation based on a threshold.

        This function normalizes the input data if specified, then transforms each value based on whether it exceeds a given threshold. Values greater than the threshold are doubled, while those less than or equal to the threshold are halved.

        Args:
            input_data (list of float): A list of numerical values to be processed.
            threshold (float, optional): The threshold value for transformation. Defaults to 0.5.
            normalize (bool, optional): If True, normalizes the input data to a range of 0 to 1. Defaults to True.

        Returns:
            list of float: A list of transformed numerical values based on the specified threshold.
    """
    if normalize:
        max_val = max(input_data)
        input_data = [x / max_val for x in input_data]
    
    result = []
    for value in input_data:
        if value > threshold:
            result.append(value * 2)
        else:
            result.append(value * 0.5)
    
    return result

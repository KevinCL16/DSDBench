INITIAL_SYSTEM_PROMPT = '''You are a cutting-edge super capable code generation LLM. You will be given a natural language query, generate a runnable python code to satisfy all the requirements in the query. You can use any python library you want. When you complete a plot, remember to save it to a png file.
'''

INITIAL_USER_PROMPT = '''Here is the query:
"""
{{query}}
"""

If the query requires data manipulation from a csv file, process the data from the csv file and draw the plot in one piece of code.

When you complete a plot, remember to save it to a png file. The file name should be """{{file_name}}""".
'''

ERROR_PROMPT = '''There are some errors in the code you gave:
{{error_message}}
please correct the errors.
Then give the complete code and don't omit anything even though you have given it in the above code.'''

ZERO_SHOT_COT_PROMPT = '''
Here is the query:
"""
{{query}}
"""

Let's think step by step when you complete the query.

When you complete a plot, remember to save it to a png file. The file name should be """{{file_name}}"""'''
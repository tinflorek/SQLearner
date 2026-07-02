from database import run_query, compare_results, print_table, clear_terminal, authorizer
from ai import generate_valid_task
import sqlite3



if __name__ == "__main__":
    task, connection = generate_valid_task("medium", "table joins")
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    table_names = [row[0] for row in cursor.fetchall()]

    correct_query = task.correct_query
    correct_output, correct_columns = run_query(cursor, correct_query)

    connection.set_authorizer(authorizer)

    #user_query = task.correct_query  # Replace this with the user's query input in a real scenario
    #user_output = run_query(cursor, user_query)
    
    while True:
        clear_terminal()

        for table_name in table_names:
            cursor.execute(f"SELECT * FROM {table_name}")
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            print(f"\n--- {table_name} ---")
            print_table(results, columns)

        print("\n--- Expected result ---")
        print_table(correct_output, correct_columns)

        print(f"\n📝 Task:\n{task.task_description}\n")

        user_query = input("Enter your SQL query: ")

        if user_query.strip().lower() == "exit":
            print("Program ended.")
            break
        
        try:
            user_results = cursor.execute(user_query).fetchall()

            if cursor.description is None:
                print("\n❌ This is not a SELECT query — this is for reading data")
                input("\nPress Enter to try again...")
                continue

            user_columns = [desc[0] for desc in cursor.description]
            print("\n--- Your result ---")
            print_table(user_results, user_columns)
        except sqlite3.DatabaseError as e:
            print(f"❌ SQL query error: {e}")
            input("\nPress Enter to try again...")
            continue
        
        is_correct = compare_results(user_results, correct_output, order_matters=task.order_matters)
        
        if is_correct:
            print("\n🎉 Well done! The result is correct.")
            break  # exit the loop after a correct answer
        else:
            print("\n❌ Incorrect result, try again.")
            input("\nPress Enter to try again...")


    connection.close()

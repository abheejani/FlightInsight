




def fetch_todo() -> dict:
    todo_list = [
        {
            "id": 1, 
            "task": "test1", 
            "status": "Todo"
        },
        {
            "id": 2, 
            "task": "Task 2", 
            "status": "Todo"},
    ]
    return todo_list

def update_task_entry(task_id: int, text: str) -> None:
    pass 

def update_status_entry(task_id: int, text: str) -> None:
    pass

def insert_new_task(text: str) -> int:
    pass
    return 1

def remove_task_by_id(task_id: int) -> None:
    pass

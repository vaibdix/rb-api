def individual_data(rb):
    try:
        return {
            "id": str(rb.get("_id", "")),
            "panid": rb.get("panid", ""),
            "name": rb.get("name", ""),
            "dob": rb.get("dob", ""),
            "is_completed": rb.get("is_completed", False),
            "is_deleted": rb.get("is_deleted", False),
            "updated_at": rb.get("updated_at", 0),
            "creation": rb.get("creation", 0)
        }
    except Exception as e:
        print(f"Error processing rb: {e}")
        return None

def all_tasks(rbs):
    return [data for rb in rbs if (data := individual_data(rb)) is not None]
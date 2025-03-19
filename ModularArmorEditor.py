from tkinter import filedialog, simpledialog, messagebox
import ttkbootstrap as ttk
import json
import uuid

from ttkbootstrap.scrolled import ScrolledText


class ModularArmorEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Modular Armor Editor")
        self.root.geometry("800x600")
        self.root.configure(bg="#1E1E1E")

        self.data = {
            "id": str(uuid.uuid4()),
            "name": "",
            "description": "",
            "hidden": [],
            "categories": []
        }
        self.currently_selected_item_id = None

        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)
        root.columnconfigure(3, weight=1)
        root.rowconfigure(2, weight=4)
        root.rowconfigure(5, weight=2)
        root.rowconfigure(8, weight=1)

        # Name
        ttk.Label(self.root, text="Mod Name:").grid(row=0, column=0, sticky='w')
        self.name_entry = ttk.Entry(self.root, width=50)
        self.name_entry.grid(row=0, column=1, columnspan=2)
        self.name_entry.bind("<FocusOut>", self.save_name)

        # Description
        ttk.Label(self.root, text="Description:").grid(row=1, column=0, sticky='w')
        self.description_entry = ttk.Entry(self.root, width=50)
        self.description_entry.grid(row=1, column=1, columnspan=2)
        self.description_entry.bind("<FocusOut>", self.save_description)

        # Categories Treeview
        self.tree = ttk.Treeview(self.root, columns="type", show="tree")
        self.tree.grid(row=2, column=0, columnspan=3, sticky='nsew')
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.tree_buttons_frame = ttk.Frame(self.root)
        self.tree_buttons_frame.grid(row=2, column=3, sticky='nsew')
        self.tree_buttons_frame.rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.tree_buttons_frame.columnconfigure(0, weight=1)

        self.add_category_btn = ttk.Button(self.tree_buttons_frame, text="Add Root Category",
                                           command=self.add_root_category)
        self.add_category_btn.grid(row=0, column=0)

        self.add_category_btn = ttk.Button(self.tree_buttons_frame, text="Add Category", command=self.add_category)
        self.add_category_btn.grid(row=1, column=0)

        self.add_entry_btn = ttk.Button(self.tree_buttons_frame, text="Add Entry", command=self.add_entry)
        self.add_entry_btn.grid(row=2, column=0)

        self.remove_btn = ttk.Button(self.tree_buttons_frame, text="Remove", command=self.remove_item)
        self.remove_btn.grid(row=3, column=0)

        self.move_up_btn = ttk.Button(self.tree_buttons_frame, text="Move Above", command=self.move_above)
        self.move_up_btn.grid(row=4, column=0)

        self.move_down_btn = ttk.Button(self.tree_buttons_frame, text="Move Below", command=self.move_below)
        self.move_down_btn.grid(row=5, column=0)

        ttk.Label(self.root, text="Option Name:").grid(row=4, column=0, sticky='w')
        self.item_entry = ttk.Entry(root)
        self.item_entry.grid(row=4, column=1, columnspan=2, sticky='nsew')
        self.item_entry.bind("<FocusOut>", self.save_item_entry)  # Save when focus is lost

        self.mesh_text = ScrolledText(self.root, height=4, wrap='word', background='#2E2E2E', foreground='white',
                                      insertbackground='white')
        self.mesh_text.grid(row=5, column=0, columnspan=3, sticky='nsew')
        self.mesh_text.bind('<FocusOut>', self.save_mesh_text)

        # Save/Load Buttons
        self.save_btn = ttk.Button(self.root, text="Save JSON", command=self.save_json)
        self.save_btn.grid(row=9, column=0)

        self.load_btn = ttk.Button(self.root, text="Load JSON", command=self.load_json)
        self.load_btn.grid(row=9, column=1)

    def on_tree_select(self, event):
        selected_item_data = self.get_selected_item_data()
        if not selected_item_data:
            return
        values = selected_item_data.get("values", [])
        if values:
            item_type, item_id = values
            self.currently_selected_item_id = item_id
            if item_type == "category":
                category = self.find_category_by_id(self.data, item_id)
                if category:
                    self.item_entry.delete(0, ttk.END)
                    self.item_entry.insert(0, category.get("label", ""))
                    self.mesh_text.text.delete("1.0", ttk.END)
            elif item_type == "entry":
                entry = self.find_entry_by_id(self.data, item_id)
                if entry:
                    self.item_entry.delete(0, ttk.END)
                    self.item_entry.insert(0, entry.get("name", ""))
                    self.mesh_text.text.delete("1.0", ttk.END)
                    for i, mesh in enumerate(reversed(entry.get("mesh", []))):
                        if i > 0:
                            self.mesh_text.text.insert("1.0", '\n')
                        self.mesh_text.text.insert("1.0", mesh)

    def get_selected_item_data(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return None
        return self.tree.item(selected_item)

    def get_selected_entry(self):
        item_data = self.get_selected_item_data()
        if not item_data:
            return None
        return self.find_entry_by_id(self.data, item_data["values"][1])

    def get_selected_category(self):
        item_data = self.get_selected_item_data()
        if not item_data:
            return None
        return self.find_category_by_id(self.data, item_data["values"][1])

    def get_selected_category_or_owning_category(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return None
        item_data = self.tree.item(selected_item)
        if not item_data:
            return None
        category = self.find_category_by_id(self.data, item_data["values"][1])
        if category is not None:
            return category

        item_data = self.tree.item(self.tree.parent(selected_item))
        category = self.find_category_by_id(self.data, item_data["values"][1])
        if category is not None:
            return category
        return None

    def add_category(self):
        # can't add category to entry
        if self.get_selected_entry():
            return
        selected_category = self.get_selected_category()
        label = simpledialog.askstring("Add Category", "Enter category label:")
        if label:
            new_category = {"id": str(uuid.uuid4()), "label": label, "entries": [], "categories": []}
            if selected_category:
                if "categories" not in selected_category:
                    selected_category["categories"] = []
                selected_category["categories"].append(new_category)
            else:
                self.data["categories"].append(new_category)
            self.refresh_tree()

    def add_root_category(self):
        label = simpledialog.askstring("Add Root Category", "Enter category label:")
        if label:
            new_category = {"id": str(uuid.uuid4()), "label": label, "entries": [], "categories": []}
            self.data["categories"].append(new_category)
            self.refresh_tree()

    def add_entry(self):
        category = self.get_selected_category_or_owning_category()
        if not category:
            return

        label = simpledialog.askstring("Add Entry", "Enter entry name:")
        if label:
            entry = {"id": str(uuid.uuid4()), "name": label, "mesh": []}
            category["entries"].append(entry)
            self.refresh_tree()

    def remove_item(self):
        item_data = self.get_selected_item_data()
        if not item_data:
            return None
        remove_result = self.remove_item_by_id(self.data, item_data["values"][1])
        if remove_result:
            self.refresh_tree()

    def move_direction(self, difference):
        index = self.tree.index(self.tree.selection())
        selected_item_parent = self.tree.parent(self.tree.selection())
        if selected_item_parent:
            item_parent_data = self.tree.item(selected_item_parent)
            if not item_parent_data:
                return None
            owning_category = self.find_category_by_id(self.data, item_parent_data["values"][1])
            if owning_category:
                entry = self.get_selected_entry()
                if entry:
                    temp = owning_category["entries"][index + difference]
                    owning_category["entries"][index + difference] = owning_category["entries"][index]
                    owning_category["entries"][index] = temp
                category = self.get_selected_category()
                if category:
                    temp = owning_category["categories"][index + difference]
                    owning_category["categories"][index + difference] = owning_category["categories"][index]
                    owning_category["categories"][index] = temp
        else:
            temp = self.data["categories"][index + difference]
            self.data["categories"][index + difference] = self.data["categories"][index]
            self.data["categories"][index] = temp
        self.refresh_tree()

    def move_above(self):
        self.move_direction(-1)

    def move_below(self):
        self.move_direction(1)

    def get_collapsed_nodes(self):
        collapsed_nodes = []
        for item in self.tree.get_children():
            collapsed_nodes.extend(self.find_collapsed_recursive(item))
        return collapsed_nodes

    def find_collapsed_recursive(self, item):
        collapsed = []
        children = self.tree.get_children(item)
        if children and not self.tree.item(item, "open"):  # Check if it has children but is collapsed
            collapsed.append(item)
        for child in children:
            collapsed.extend(self.find_collapsed_recursive(child))
        return collapsed

    def save_json(self):
        self.data["id"] = str(uuid.uuid4())
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump(self.data, f, indent=4)

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as f:
                self.data = json.load(f)
            self.refresh_tree()

    def refresh_tree(self):
        collapsed_ids = []
        for node in self.get_collapsed_nodes():
            item_data = self.tree.item(node)
            if not item_data:
                continue
            collapsed_ids.append(item_data["values"][1])

        self.tree.delete(*self.tree.get_children())

        def populate_tree(parent, categories):
            for category in categories:
                cat_id = category["id"]
                cat_label = category["label"]
                cat_item = self.tree.insert(parent, "end", text=cat_label, values=("category", cat_id))
                populate_tree(cat_item, category.get("categories", []))
                for entry in category.get("entries", []):
                    self.tree.insert(cat_item, "end", text=entry["name"], values=("entry", entry["id"]))

        populate_tree("", self.data["categories"])

        def open_children(parent):
            item_data = self.tree.item(parent)
            if not item_data:
                return
            if item_data["values"][1] not in collapsed_ids:
                self.tree.item(parent, open=True)
            for _child in self.tree.get_children(parent):
                open_children(_child)

        children = self.tree.get_children('')
        for child in children:
            open_children(child)

        self.name_entry.delete(0, ttk.END)
        self.name_entry.insert(0, self.data["name"])
        self.description_entry.delete(0, ttk.END)
        self.description_entry.insert(0, self.data["description"])

    def find_category_by_id(self, data, category_id):
        for category in data["categories"]:
            if category["id"] == category_id:
                return category
            if "categories" in category:
                found = self.find_category_by_id(category, category_id)
                if found:
                    return found
        return None

    def find_entry_by_id(self, data, entry_id):
        for category in data["categories"]:
            for entry in category.get("entries", []):
                if entry["id"] == entry_id:
                    return entry
            if "categories" in category:
                found = self.find_entry_by_id(category, entry_id)
                if found:
                    return found
        return None

    def remove_item_by_id(self, data, item_id) -> bool:
        for category_index, category in enumerate(data["categories"]):
            if category["id"] == item_id:
                data["categories"].pop(category_index)
                return True
            for entry_index, entry in enumerate(category.get("entries", [])):
                if entry["id"] == item_id:
                    category["entries"].pop(entry_index)
                    return True
            if "categories" in category:
                rec_remove_result = self.remove_item_by_id(category, item_id)
                if rec_remove_result:
                    return True
        return False

    def save_mesh_text(self, event=None):
        text_list = self.mesh_text.text.get('1.0', 'end').replace(" ", "").split('\n')
        text_list = [s for s in text_list if s.strip()]

        entry = self.find_entry_by_id(self.data, self.currently_selected_item_id)

        if not entry:
            return

        if text_list != entry["mesh"]:
            entry["mesh"] = text_list
            self.selected_mesh_entry_index = None
            self.on_tree_select({})

    def save_item_entry(self, event=None):
        """Save the edited item back to the list and update the treeview."""
        if hasattr(self, 'currently_selected_item_id'):
            new_value = self.item_entry.get()

            entry = self.find_entry_by_id(self.data, self.currently_selected_item_id)
            if entry:
                if new_value != entry["name"]:
                    entry["name"] = new_value
                    self.currently_selected_item_id = None
                    self.refresh_tree()

            category = self.find_category_by_id(self.data, self.currently_selected_item_id)
            if category:
                if new_value != category["label"]:
                    category["label"] = new_value
                    self.currently_selected_item_id = None
                    self.refresh_tree()

    def save_name(self, event=None):
        self.data["name"] = self.name_entry.get()

    def save_description(self, event=None):
        self.data["description"] = self.description_entry.get()


if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = ModularArmorEditor(root)
    root.mainloop()

from tkinter import *
from tkinter import ttk
from control import get_card_info
from model import (
    collection, 
    init_database, 
    record_from_card, 
    persist_collection, 
    load_collection,
    close_database,
    add_user as model_add_user,
    remove_user as model_remove_user,
    get_all_users,
    load_users,
    get_user_count
)
from PIL import ImageTk, Image
import urllib.request
import io


# GLOBAL VIEW STATE ==============================================================================#
name = None
set_info = None
card_type = None
rarity = None
market = None
photo = None
last_card = None
user_array = ["No Users"]

filter_field_options = ("Name", "Set", "Rarity")
filter_field_var = None
filter_text_var = None
#=================================================================================================#


# NAVIGATION FUNCTIONS ===========================================================================#
def show_start():
    """Show the start/collection page."""
    for p in pages:
        p.pack_forget()
    page = pages[0]
    page.pack()


def show_add():
    """Show the add card page."""
    for p in pages:
        p.pack_forget()
    page = pages[1]
    page.pack()


def show_users():
    """Show the users page."""
    for p in pages:
        p.pack_forget()
    page = pages[2]
    page.pack()
#=================================================================================================#


# CARD SEARCH AND DISPLAY FUNCTIONS ==============================================================#
def update_add_view():
    """Update the add page with current card info."""
    pokemon_image.config(image=photo) 
    pokemon_name.config(text=f"Card Name: {name}")
    pokemon_type.config(text=f"Card Type: {card_type}")
    pokemon_rarity.config(text=f"Rarity: {rarity}")
    pokemon_market.config(text=f"Market Price: ${market}")


def add_card(event=None):
    """Search for a card and display it on the add page."""
    query = entry.get()
    if(query):
        card_info = get_card_info(query)
        
        if card_info:
            global name, set_info, card_type, rarity, market, photo, last_card
            name = card_info.get("name", "Unknown")
            set_info = card_info.get("setName", "Unknown Set")
            card_type = card_info.get("cardType")
            rarity = card_info.get("rarity", "Unknown Rarity")
            img_url = card_info.get("imageUrl")
            prices = card_info.get("prices", {})
            if isinstance(prices, dict) and prices:
                market = prices.get("market")

            # Try to load image, but do not fail if network is blocked
            photo = None
            if img_url:
                try:
                    with urllib.request.urlopen(img_url) as u:
                        raw_data = u.read()
                    image = Image.open(io.BytesIO(raw_data))
                    photo = ImageTk.PhotoImage(image)
                except Exception:
                    photo = None

            last_card = card_info
            update_add_view()
        else:
            print("No card found with that name or ID.\n")
    else:
        print("Please enter a card name or ID.")


def save_current_card():
    """Save the current card to the collection."""
    if not last_card:
        print("Search a card first before saving.")
        return
    rec = record_from_card(last_card)
    collection.append(rec)
    persist_collection()
    refresh_collection_view()
    entry.delete(0, END)
    show_start()
#=================================================================================================#


# COLLECTION VIEW FUNCTIONS ======================================================================#
def refresh_collection_view():
    """Refresh the collection treeview."""
    # Clear tree rows
    for row in collection_tree.get_children():
        collection_tree.delete(row)
    # Insert records
    for idx, rec in enumerate(collection):
        price = rec.get("market")
        price_str = f"${price}" if isinstance(price, (int, float)) else (f"${price}" if price else "-")
        tag = "odd" if idx % 2 else "even"
        collection_tree.insert("", "end", iid=str(idx), values=(rec.get("name"), rec.get("set"), rec.get("rarity"), price_str), tags=(tag,))
    # Update total
    total = 0.0
    for rec in collection:
        p = rec.get("market")
        try:
            if p is not None:
                total += float(p)
        except (TypeError, ValueError):
            pass
    total_value_lbl.config(text=f"Total Value: ${total:,.2f}")


def remove_selected():
    """Remove selected cards from the collection."""
    selected = collection_tree.selection()
    if not selected:
        return
    # Remove from end to start to maintain indices
    for iid in sorted((int(s) for s in selected), reverse=True):
        if 0 <= iid < len(collection):
            collection.pop(iid)
    persist_collection()
    refresh_collection_view()
#=================================================================================================#


# FILTER FUNCTIONS ===============================================================================#
def apply_collection_filter(event=None):
    """Apply filter to collection view (stub)."""
    field = filter_field_var.get()
    text = filter_text_var.get().strip()
    print(f"Filter stub — Field: {field}, Text: '{text}' (not implemented)")


def clear_collection_filter():
    """Clear the filter."""
    filter_field_var.set("Name")
    filter_text_var.set("")
    refresh_collection_view()
#=================================================================================================#


# USER MANAGEMENT FUNCTIONS ======================================================================#
def add_user():
    """Add a new user to the listbox."""
    username = new_user_entry.get().strip()
    if username:
        success, message = model_add_user(username)
        if success:
            user_listbox.insert(END, username)
            new_user_entry.delete(0, END)
            update_user_stats()
            refresh_users_view()
        else:
            print(message)
    else:
        print("Please enter a username.")


def remove_user():
    """Remove selected user from the listbox."""
    selection = user_listbox.curselection()
    if selection:
        username = user_listbox.get(selection[0])
        success, message = model_remove_user(username)
        if success:
            user_listbox.delete(selection[0])
            update_user_stats()
            refresh_users_view()
        else:
            print(message)
    else:
        print("Please select a user to remove.")


def update_user_stats():
    """Update the total users count."""
    count = get_user_count()
    total_users_lbl.config(text=f"Total Users: {count}")


def refresh_users_view():
    """Refresh the users listbox from the model."""
    global user_array
    user_listbox.delete(0, END)
    user_array.clear()
    for user in get_all_users():
        user_listbox.insert(END, user.get("username"))
        user_array.append(user.get("username"))
    menu = users_menu["menu"]
    menu.delete(0, "end")
    for item in user_array:
        menu.add_command(label=item, command=lambda value=item: clicked.set(value))
    if not user_array:
        clicked.set("No Selected User")
    update_user_stats()
#=================================================================================================#


# INITIALIZE WINDOW ==============================================================================#
root = Tk()
root.geometry('1920x1080')
root.title("Pokemon Card Manager")

filter_field_var = StringVar(master=root, value="Name")
filter_text_var = StringVar(master=root, value="")

# Main frame
main_frame = Frame(root)
#=================================================================================================#


# START PAGE =====================================================================================#
start = Frame(main_frame)

title = Label(start,text="Welcome to the Pokemon Card Manager")
title.grid(row=0, column=0, sticky='w')

add_button = Button(start, text="ADD CARD", width=12, command=show_add)
add_button.grid(row=0, column=2, sticky='e')

user_button = Button(start, text = "User Page", command=show_users)
user_button.grid(row=0, column=1, sticky='w')

# Filter frame
filter_frame = Frame(start)
filter_frame.grid(row=1, column=0, columnspan=2, sticky='we', padx=12, pady=(5, 16))

filter_label = Label(filter_frame, text="Filter:")
filter_label.grid(row=0, column=0, padx=(0, 8), sticky='w')

filter_field = ttk.Combobox(filter_frame,
                            values=filter_field_options,
                            textvariable=filter_field_var,
                            state="readonly",
                            width=12,
                            justify="center")
filter_field.grid(row=0, column=1, padx=(0, 8))

filter_entry = Entry(filter_frame,
                     textvariable=filter_text_var,
                     width=24,
                     highlightthickness=0,
                     )
filter_entry.grid(row=0, column=2, padx=(0, 8))
filter_entry.bind("<Return>", apply_collection_filter)

filter_btn = Button(filter_frame, text="FILTER", command=apply_collection_filter)
filter_btn.grid(row=0, column=3, padx=(0, 6))

clear_btn = Button(filter_frame, text="CLEAR", command=clear_collection_filter)
clear_btn.grid(row=0, column=4)

clicked = StringVar()
clicked.set("No Selected User")
users_menu = OptionMenu(filter_frame, clicked, *user_array)
users_menu.grid(row=0, column=6, padx=(50, 6))

# Collection list
columns = ("Name", "Set", "Rarity", "Market Value")
collection_tree = ttk.Treeview(start, columns=columns, show="headings", height=20)
for col in columns:
    collection_tree.heading(col, text=col)
    collection_tree.column(col, anchor='w', width=140)
collection_tree.grid(row=2, column=0, columnspan=2, padx=(12, 0), sticky='nsew')

total_value_lbl = Label(start,text="Total Value: $0.00")
total_value_lbl.grid(row=3, column=0, sticky='w', padx=12, pady=12)

remove_btn = Button(start, text="REMOVE SELECTED", command=remove_selected)
remove_btn.grid(row=3, column=1, sticky='e', padx=12, pady=12)
#=================================================================================================#


# ADD PAGE =======================================================================================#
add = Frame(main_frame)

entry_label = Label(add,text="Enter TCGplayer ID or Card Name")
entry_label.grid(row=1, column=0, padx=5)

entry = Entry(add, width=15, highlightthickness=0)
entry.grid(row=1, column=1)
entry.bind("<Return>", add_card)

entry_search = Button(add, text="ADD", width=6, command=add_card)
entry_search.grid(row=1, column=2)

back_btn = Button(add, text="BACK", command=show_start)
back_btn.grid(row=0, column=0, sticky='w', padx=10, pady=10)

save_btn = Button(add, text="SAVE TO COLLECTION", command=save_current_card)
save_btn.grid(row=0, column=2, sticky='e', padx=10, pady=10)

pokemon_image = Label(add, image=photo)
pokemon_image.grid(row=2, column=0, columnspan=3)

pokemon_name = Label(add, text=f"")
pokemon_name.grid(row=3, column=0, columnspan=3)

pokemon_type = Label(add, text=f"")
pokemon_type.grid(row=4, column=0, columnspan=3)

pokemon_rarity = Label(add, text=f"")
pokemon_rarity.grid(row=5, column=0, columnspan=3)

pokemon_market = Label(add,text=f"")
pokemon_market.grid(row=6, column=0, columnspan=3)
#=================================================================================================#

main_frame.pack(fill=BOTH, expand=True)

# USERS PAGE =====================================================================================#
users = Frame(main_frame)

# Title
users_title = Label(users, text="User Management", font=("Arial", 16, "bold"))
users_title.grid(row=0, column=0, columnspan=3, pady=(10, 20))

# Back button
users_back_btn = Button(users, text="BACK", command=show_start)
users_back_btn.grid(row=0, column=0, sticky='w', padx=10, pady=10)

# User list frame
user_list_frame = Frame(users)
user_list_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=10, sticky='nsew')

# User listbox with scrollbar
user_listbox_label = Label(user_list_frame, text="Registered Users:")
user_listbox_label.pack(anchor='w', pady=(0, 5))

user_scrollbar = Scrollbar(user_list_frame)
user_scrollbar.pack(side=RIGHT, fill=Y)

user_listbox = Listbox(user_list_frame, height=15, width=40, yscrollcommand=user_scrollbar.set)
user_listbox.pack(side=LEFT, fill=BOTH, expand=True)
user_scrollbar.config(command=user_listbox.yview)

# Add/Remove user controls
user_control_frame = Frame(users)
user_control_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=20)

new_user_label = Label(user_control_frame, text="Username:")
new_user_label.grid(row=0, column=0, padx=5)

new_user_entry = Entry(user_control_frame, width=20, highlightthickness=0)
new_user_entry.grid(row=0, column=1, padx=5)
new_user_entry.bind("<Return>", lambda e: add_user())

add_user_btn = Button(user_control_frame, text="ADD USER", width=12, command=add_user)
add_user_btn.grid(row=0, column=2, padx=5)

remove_user_btn = Button(user_control_frame, text="REMOVE SELECTED", width=15, command=remove_user)
remove_user_btn.grid(row=1, column=0, columnspan=3, pady=10)

# User stats frame
user_stats_frame = Frame(users)
user_stats_frame.grid(row=3, column=0, columnspan=3, padx=20, pady=10)

total_users_lbl = Label(user_stats_frame, text="Total Users: 0")
total_users_lbl.pack()
#=================================================================================================#

pages = [start, add, users]

# INITIALIZE APP =================================================================================#
init_database()
load_collection()
load_users()
show_start()
refresh_collection_view()
refresh_users_view()

# Cleanup on close
def on_closing():
    close_database()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
#=================================================================================================#
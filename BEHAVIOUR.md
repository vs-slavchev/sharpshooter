# Sharpshooter — Behaviour

This file describes what Sharpshooter does from the user's point of view. It covers what the user wants to get done, the actions available to them, and how the program responds. Implementation details are left out on purpose. Key names refer to the default bindings, and every binding can be changed (see *Configure the tool*).

---

## Who it is for

Someone who works in a terminal and wants to move around folders and handle files with single keystrokes, without leaving the keyboard or memorising shell commands. The tool aims to stay small, predictable and easy to change.

## Jobs to be done

1. **See where I am and what is around me** – the current folder, its parent and what is inside the selected item.
2. **Move through the file system quickly** – up, down, into and out of folders.
3. **Organise files** – create, rename, copy, move and delete them, alone or in groups.
4. **Recover from mistakes** – undo a delete.
5. **Hand off to other tools** – open a file in its default app, open a terminal here, copy a name to paste elsewhere.
6. **Pack and unpack** – make zip archives and extract them.
7. **Shape the tool to my habits** – choose my own keys and keep my view preferences.

---

## 1. Seeing where I am

**Scenario: Starting the program**
- Given I launch Sharpshooter
- Then the current folder is my home folder
- And the first item in it is selected

**Scenario: Three-pane view**
- Given I am in a folder
- Then the top line shows the full path of the current folder
- And the left pane lists the parent folder's contents, with the current folder highlighted
- And the middle pane lists the current folder's contents, with one item selected
- And the right pane shows the contents of the selected item if it is a folder, and stays empty if it is a file
- And below the panes, a status line describes the last action
- And the bottom line shows the hotkey guide, unless I have hidden it

**Scenario: At the root of the file system**
- Given the current folder is the root
- Then the left pane is empty

**Scenario: How items are listed**
- Folders come first, then files, each group sorted alphabetically
- Folder names end with a slash and are coloured
- Ordinary items are bold, and hidden items (names starting with a dot) use normal weight
- Marked items are underlined, and the selected item is shown in reverse video
- Symbolic links, sockets and pipes are not listed
- A folder I am not allowed to read looks empty
- Names too long for the pane are cut short and end with "..."

**Scenario: Long folders**
- Given a folder has more items than fit in the pane
- When I move the selection past the visible edge
- Then the list scrolls so the selection stays visible

## 2. Moving around

**Scenario: Move the selection**
- When I press `n` or Down, the next item is selected
- When I press `e` or Up, the previous item is selected
- And moving past the last item wraps to the first, and past the first wraps to the last
- And in an empty folder nothing happens

**Scenario: Enter a folder**
- Given a folder is selected
- When I press `i`, Right or Enter
- Then that folder becomes the current folder and its first item is selected
- And all marks are cleared
- And the status line is cleared

**Scenario: Try to enter a file**
- Given a file is selected
- When I press `i` or Right
- Then nothing happens

**Scenario: Go up to the parent**
- Given I am not at the root
- When I press `k` or Left
- Then the parent becomes the current folder
- And the folder I just left is selected
- And all marks are cleared, and the status line is cleared

## 3. Showing and hiding hidden files

**Scenario: Toggle hidden files**
- When I press `h`
- Then hidden items appear if they were hidden, or disappear if they were shown
- And the choice is saved and used the next time I start the program

**Scenario: The selection survives the toggle**
- Given a visible item is selected
- When I toggle hidden files
- Then the same item stays selected, even if its position in the list changed

**Scenario: Hiding the selected hidden item**
- Given a hidden item is selected
- When I hide hidden files
- Then the nearest visible item is selected instead (first looking above, then below)

**Scenario: Marks survive the toggle**
- Given some items are marked
- When I toggle hidden files
- Then marked items that are still visible stay marked
- And marked items that become hidden are unmarked

**Scenario: The current folder is itself hidden**
- Given I am inside a hidden folder and hidden files are not shown
- Then the left pane still lists that folder so I can see where I am

## 4. Selecting several items

**Scenario: Mark and unmark**
- When I press `m` on an unmarked item, it becomes marked
- When I press `m` on a marked item, it becomes unmarked
- And I can mark any number of items in the current folder

**Scenario: Actions on marked items**
- Given at least one item is marked
- Then copy, cut, delete and zip act on all marked items instead of only the selected one

**Scenario: Marks are tied to a folder**
- When I enter another folder or go up to the parent, all marks are cleared

## 5. Creating and renaming

**Scenario: Create a folder**
- When I press `f`
- Then an empty input line appears below the last item
- When I type a name and press Enter
- Then a folder with that name is created in the current folder and selected
- And the status line reads "Made new folder [name]."

**Scenario: Create a folder that already exists**
- Given an item with that name already exists
- When I try to create it
- Then nothing is created and the status line reports that it already exists

**Scenario: Create a folder without permission**
- Then nothing is created and the status line reports missing permissions

**Scenario: Rename**
- Given an item is selected
- When I press `r`
- Then an input line appears over the selected item, prefilled with its current name
- When I edit the name and press Enter
- Then the item is renamed and the status line reads "Renamed [old] to [new]."

**Scenario: Cancel input**
- Given an input line is open (for a new folder or a rename)
- When I press Escape
- Then nothing changes

**Scenario: Input cleanup**
- Leading and trailing spaces, slashes, quotes, commas and newlines are removed from what I type

**Scenario: Rename in an empty folder**
- Then nothing happens

## 6. Copying and moving

**Scenario: Copy**
- When I press `c`
- Then the selected item (or all marked items) goes on the internal clipboard
- And the status line reads "Clipboard: [name]." or "Clipboard: N files."

**Scenario: Cut**
- When I press `d`
- Then it works like copy, except that pasting will move the items instead of copying them

**Scenario: Paste**
- Given the clipboard has items and I am in some folder
- When I press `p`
- Then the items are copied (or moved, after a cut) into the current folder
- And if one item was pasted, it becomes selected and the status line reads "Pasted [name]."
- And if several items were pasted, the first line is selected and the status line reads "Pasted N files."
- And the clipboard is emptied and all marks are cleared

**Scenario: Pasting a copy over an existing name**
- Given an item with the same name already exists in the destination
- When I paste a copy
- Then the new item gets "_copy" added to its name, again and again until the name is unique

**Scenario: Paste fails**
- Given I am not allowed to write to the destination
- When I paste
- Then the status line reports the missing permission, and the clipboard is emptied

**Scenario: Paste with an empty clipboard**
- Then nothing happens

**Scenario: Copy or cut in an empty folder**
- Then nothing happens

## 7. Deleting and undoing

**Scenario: Delete**
- When I press `x`
- Then the selected item (or all marked items) is moved to the system trash, not permanently removed
- And the status line reads "Deleted [name]." or "Deleted N files."
- And the selection stays at the same position, or moves to the new last item
- And all marks are cleared

**Scenario: Trash conventions**
- On Linux, deleted items go to the desktop trash with the metadata file managers expect, so they can be restored from there too
- On macOS, deleted items go to the user's Trash
- If an item with the same name is already in the trash, the new one gets a timestamp added to its name

**Scenario: Delete fails**
- Given I am not allowed to move the item
- Then it stays where it is and the status line reports the problem

**Scenario: Undo a delete**
- Given I have deleted items during this session
- When I press `u`
- Then the most recently deleted item goes back to where it was
- And the status line reads "Undone delete of [name]."
- And pressing `u` again restores the one deleted before that, up to the last 128 deletes

**Scenario: Nothing to undo**
- Given nothing has been deleted this session
- When I press `u`
- Then nothing happens

**Scenario: Undo covers deletes only**
- Renames, pastes, moves and new folders cannot be undone

**Scenario: Delete in an empty folder**
- Then nothing happens

## 8. Archives

**Scenario: Zip one item**
- Given a non-zip item is selected and nothing is marked
- When I press `z`
- Then a zip archive named after the item is created next to it in the background
- And while it is being made, the archive appears in the list prefixed with "[zipping...]"
- And I can keep working while it runs

**Scenario: Zip marked items**
- Given several items are marked
- When I press `z`
- Then they are packed together into an archive named "archive_" followed by the date and time
- And the marks are cleared

**Scenario: Unzip**
- Given a ".zip" file is selected
- When I press `z`
- Then it is extracted in the background into a new folder named after the archive without ".zip"

**Scenario: One zip at a time**
- Given an archive is still being made
- When I press `z` again
- Then nothing happens

## 9. Handing off to other tools

**Scenario: Open a file**
- Given a file is selected
- When I press Enter
- Then it opens in the system's default application for that file type
- And Sharpshooter stays open and responsive

**Scenario: Open a terminal here**
- When I press `t`
- Then a new terminal window opens with the current folder as its working directory
- And on Linux the desktop's own terminal is tried first, followed by common terminals that are installed
- And on macOS iTerm is used if I am already running it, and Terminal otherwise

**Scenario: Copy a name**
- Given an item is selected
- When I press `y`
- Then its name (without the trailing slash for folders) is put on the system clipboard
- And the status line reads "Copied [name] to clipboard."
- And on Linux this needs xclip or xsel, and if neither is installed nothing is copied

## 10. Help and quitting

**Scenario: Hotkey guide**
- Given the guide is visible
- Then the bottom line lists the editing and utility actions with their keys
- And when an action's name contains its key, the key is shown in brackets inside the name, for example "(r)ename"

**Scenario: Toggle the hotkey guide**
- When I press `?`
- Then the guide is hidden if it was shown, or shown if it was hidden
- And the choice is saved for the next start

**Scenario: Quit**
- When I press `q`
- Then the program exits and the terminal goes back to normal

**Scenario: Unbound keys**
- When I press a key that is not bound to anything
- Then nothing happens

## 11. Configuring the tool

**Scenario: First run**
- Given no configuration file exists
- When I start the program
- Then a configuration file with the defaults is created in my home folder

**Scenario: Rebind keys**
- Given I edit the configuration and give an action a different key
- When I restart the program
- Then the new key performs that action, and the hotkey guide shows the new key
- And actions I did not mention keep their default keys

**Scenario: Duplicate binding**
- Given two actions are bound to the same key
- When I start the program
- Then it refuses to start, names both actions and the key, and tells me how to fix it

**Scenario: Invalid setting**
- Given a yes/no setting has a value other than True or False
- When I start the program
- Then it refuses to start, names the setting and the bad value, and tells me how to fix it

**Scenario: Corrupt configuration**
- Given the configuration file cannot be read
- When I start the program
- Then it refuses to start and suggests fixing the syntax or deleting the file to reset to defaults

**Scenario: Remembered preferences**
- Whether hidden files are shown and whether the hotkey guide is visible are saved whenever I toggle them
- If saving fails, the program carries on and the preference applies only for this session

## Default keys

| Action | Key |
|---|---|
| Move down / up | `n` / `e` (or arrow keys) |
| Go to parent / enter folder | `k` / `i` (or Left / Right) |
| Open file or enter folder | Enter |
| New folder | `f` |
| Rename | `r` |
| Copy / cut / paste | `c` / `d` / `p` |
| Delete | `x` |
| Undo delete | `u` |
| Mark item | `m` |
| Zip / unzip | `z` |
| Copy name to clipboard | `y` |
| Toggle hidden files | `h` |
| Open terminal here | `t` |
| Toggle hotkey guide | `?` |
| Quit | `q` |

## Out of scope

These are deliberately not supported: bulk rename, special encodings or alphabets, file previews beyond listing a folder's contents, multiple tabs, and plugins.

## What is Pynab?

Pynab is a Python interface to the YNAB4 (You Need A Budget v4) database. The purpose is to give an interface for other scripts to use to analyze or automate some tasks that would otherwise be time-consuming. This would also give users the ability to add some features, theoretically, to YNAB.

## History
This project started as a fork of James Seward's alfred-ynab Alfred 2 module, [https://github.com/jamesoff/alfred-ynab](https://github.com/jamesoff/alfred-ynab). He included a YNAB parser for the purposes of finding the remaining budget balances for the Alfred workflow.

This was only a read-only interface, and I wanted to create an interface that would allow for writing to the database. This would enable the automation of transaction entry, tracking investments by increase / decrease transactions, etc.

## Development
The [wiki](https://github.com/elaske/pynab/wiki) for this project will house any information relevant to development or use. During development, I plan to store any information I find from reverse-engineering the YNAB database in the wiki. Also, eventually, this will be where the information as to how to use this library will be located.

## License
The original interface was licensed BSD. Whilst this remains in the repository in any form, I will be licensing this in BSD as well.

## Contributing
If anyone has any interest in contributing, please contact me. You can suggest a feature by adding an issue if you so desire as well.

**Disclaimer:** I am but a lone contributor and can only work on this in my spare free time. The day job does get in the way of things like this. So, I make no guarantees as to the timeliness of completion, etc.

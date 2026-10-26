# Credits and prior art

This work stands on others'. Please read them; they know things this repository does not.

- **KOReader** and the contributors of its Bookeen/Cybook port (koreader and koreader-base `bookeen` target, and the
  open upstream PR for Cybook Muse support): <https://github.com/koreader/koreader>. The "Saraiva Lev com luz
  (CYBOY4F-SA)" is already listed in the port's device file.
- **Soutadé**, "Game Over" and the Cybook firmware/ADB research: <https://blog.soutade.fr/post/2015/03/game_over.html>
  (the ADB-on-the-Cybook method that this project used comes from there).
- **br-lemes**, earlier work on this device family: <https://github.com/br-lemes/lev-jailbreak> and
  <https://www.br-lemes.net/2017/03/ssh-no-lev.html> (SSH on the Lev). The author of this repository did not
  review that work in depth, so check it for things that were missed here.
- **linux-sunxi** wiki page for the Bookeen Muse (Allwinner A13 notes, UART pins, FEL): <https://linux-sunxi.org/Bookeen_Muse>
- MobileRead forum threads on the Cybook firmware: <https://www.mobileread.com/forums/showthread.php?t=276731>
  and <https://mobileread.com/forums/showthread.php?p=4173147>.
- Hardware notes on the Cybook Odyssey HD FrontLight: <https://wiki.mobileread.com/wiki/Cybook_Odyssey_HD_FrontLight>.

## How this was made

Done by one person on their own device, in a long working session with an AI assistant (Claude, by Anthropic):
the assistant read and disassembled the stock binaries on the PC, proposed each change, and ran the commands the
owner approved one at a time, with backups. Every claim in these docs was checked on the device or marked as a
hypothesis. Names and trademarks (Saraiva, Bookeen, Cybook, KOReader, Allwinner) belong to their owners; this
project is unaffiliated.

# Solver Pro

A simple calculator/CAS application to help you with organizing and solving your algebraic equations, with a feel inspired by `ipython`. Easy to install and use out-of-the-box. You don't need to be a computer pro to do it with Solver Pro!


## Installation
Installing Solver Pro is easy! Just follow the instructions for your operating system below. If you're having problems, try checking out [the FAQ section](#faq) for answers.

### macOS
1. Download the [latest release](https://github.com/skylon07/SolverPro/releases/latest/download/SolverPro.tgz) for Solver Pro
2. Double-click the `SolverPro.tgz` file to decompress it
3. (First run only) Right-click the `SolverPro` executable and click "Open", then when the security prompt comes up, click [Open] again
   - If you're wondering what that security prompt was, [here's some info on that](#why-does-my-computer-say-that-windows-protected-your-pcsolver-pro-is-an-application-downloaded-from-the-internet-is-it-dangerous)
4. Run the `SolverPro` executable!
   - You might need to [check this out](#why-does-the-window-have-weird-charactershave-weird-colorsjust-look-wrong) if things don't look right

### Windows
1. Download the [latest release](https://github.com/skylon07/SolverPro/releases/latest/download/SolverPro.exe) for Solver Pro
2. Run the `SolverPro.exe` executable.
3. (First run only) When "Windows protected your PC" pops up, click "<u>More Info</u>" and then the [Run anyway] button at the bottom
   - If you're wondering why Windows thinks it needs to "protect you", [here's some info on that](#why-does-my-computer-say-that-windows-protected-your-pcsolver-pro-is-an-application-downloaded-from-the-internet-is-it-dangerous)
   - You might need to [check this out](#why-does-the-window-have-weird-charactershave-weird-colorsjust-look-wrong) if things don't look right



### Build from source
Well, if you insist you want to do this, go right ahead! Just note there's some assembly required! (Oh wait, sorry, not [that kind](https://en.wikipedia.org/wiki/Assembly_language); hope I didn't make you hyperventilate.)

1. Make sure you have these command line tools installed (really easy when you use [Homebrew](https://brew.sh/) on Mac):
    - `python3`/`python` (version 3.10)
    - `git`
    - `pipenv`/`pip`
2. Clone this repository: `git clone https://github.com/skylon07/SolverPro.git <target directory>`
3. Install the python libraries: `pipenv install --dev`
4. Navigate to the build directory:
    - Mac: `cd <target directory>/build-scripts/mac/`
    - Windows: `cd <target directory>/build-scripts/win`
5. Run the build script:
    - Mac: `./run_pyinstaller.sh`
    - Windows: `run_pyinstaller.exe`
6. Retrieve the application from `dist/`:
    - Mac: `dist/SolverPro`
    - Windows: `dist/SolverPro.exe`


## FAQ

### Why does my computer say that "Windows protected your PC"/"Solver Pro is an application downloaded from the internet..."? Is it dangerous?
No, it's not dangerous. Solver Pro was built using a tool called `pyinstaller`. Apple and Windows both have many safeguards in place to ensure that their users aren't downloading and running malicious software, like viruses. If you're using a Mac, you are seeing this prompt because a security tool called [Gatekeeper](https://support.apple.com/en-us/HT202491) recognized that the app wasn't signed and verified by Apple (which getting them to do costs much $$$ from me). `pyinstaller` just skips this signing process when I build the app, hence why Gatekeeper pops up the warning when you try to run it. If you're using a Windows machine, it comes with a similar software called Windows Defender with a similar signing/verification process. Again, `pyinstaller` doesn't do any software verification (the reason also being $$$ and that I'd rather spend time improving the app) -- it just compiles my python code down into a single standalone executable so you can easily run it. So as long as you trust my program wasn't written with bad intentions, you're okay to open it. Or, if you really want to, you can [build the application from source](#build-from-source) instead.

### Why does the window have weird characters/have weird colors/just look wrong?
Solver Pro uses a UI library called [Textual](https://github.com/textualize/textual/), which can sometimes have issues when certain terminals or old fonts are used. But even if things look strange, these issues are *strictly graphical* and won't inhibit the actual functionality of the application. You can try the fixes below for your operating system to see if it helps:

#### macOS:
Try following the instructions below, or follow [these instructions](https://textual.textualize.io/FAQ/#why-doesnt-textual-look-good-on-macos) straight from the Textual docs. I suggest downloading iTerm2, since it is free and works out-of-the-box with the Terminal settings you might already have, and produces a much better result than messing with the font settings.
  1. Download [iTerm2](https://iterm2.com/downloads.html) or another terminal of your choice
  2. Right-click the `SolverPro` executable file
  3. Click "Get Info"
  4. About halfway down, look for a section titled "Open with:"
  5. Click the dropdown and select the terminal application you downloaded (if you don't see it, try clicking "Other...")
  6. You can now run the `SolverPro` executable file with better graphics!

#### Windows:
The command prompt doesn't have much native support for modern character sets and terminal features, so Textual just looks terrible in it. Microsoft's "Windows Terminal" will produce much better results.
 1. Download [Windows Terminal](https://apps.microsoft.com/store/detail/windows-terminal/9N0DX20HK701) from the Microsoft Store
 2. Open the "Settings" application
 3. Type "terminal" in the search bar
 4. Click on "Terminal settings"
 5. Click "Yes" to allow system settings changes
 6. Look for the "Terminal" section towards the bottom
 7. Click the dropdown
 8. Select "Windows Terminal" (note this will change it for *all* applications that request to run in a command prompt)
 9. You can now run the `SolverPro.exe` executable file with better graphics!

### Can I use Solver Pro to do my math homework for me?
Preferrably not *for* you, no. However, I personally use many computer programs to aid me in my math work. Use it responsibly. So long as it's a tool for education and not cheating, using it is good in my books. And if you're older and haven't been to school in years, then I'm not sure why you read this Q/A to begin with.

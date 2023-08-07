# Solver Pro

A simple calculator/CAS application to help you with organizing and solving your algebraic equations. Easy (hopefully) to install and use out-of-the-box. You don't need to be a math pro to do it with Solver Pro!


## Installation
Installing Solver Pro is easy! Just follow the instructions for your operating system below:

### macOS
1. Download the [latest release](https://github.com/skylon07/SolverPro/releases/latest/download/SolverPro.tgz) for Solver Pro
2. Double-click the `SolverPro.tgz` file to decompress it
3. (First run only) Right-click the `SolverPro` application and click "Open", then when the security prompt comes up, click [Open] again
   - If you're wondering what that security prompt was, [here's some info on that](#why-does-my-mac-say-that-solver-pro-is-an-application-downloaded-from-the-internet-is-it-dangerous)
4. Double-click the `SolverPro` application to run it!

### Windows
1. Download the [latest release](https://github.com/skylon07/SolverPro/releases/latest/download/SolverPro.exe) for Solver Pro
2. Run the `SolverPro.exe` executable.
3. (First run only) When "Windows protected your PC" pops up, click "<u>More Info</u>" and then the [Run Anyway] button at the bottom
   - If you're wondering why Windows thinks it needs to "protect you", [here's some info on that](#why-does-my-mac-say-that-solver-pro-is-an-application-downloaded-from-the-internet-is-it-dangerous)

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

### Can I use Solver Pro to do my math homework for me?
Preferrably not *for* you, no. However, I personally use many computer programs to aid me in my math work. Use it responsibly. So long as it's a tool for education and not cheating, using it is good in my books. And if you're older and haven't been to school in years, then I'm not sure why you read this Q/A to begin with.

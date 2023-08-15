# How to Build (and Release)!

1. Update `getVersion()` string (in `src/common/functions.py`)
2. Start `pipenv shell`
3. `cd` to `build-scripts/mac` (or `.../win`) and run `./run_pyinstaller.sh`
4. (Mac only) run `./maketar.sh`
   - This is done since executables only retain their `chmod +x` status when using tarballs
5. Navigate to GitHub tags/releases page
6. Create a new release
7. Upload `.tgz`/`.exe` (*NOT* raw Unix executable!) as attachments to the release

# How to Build (and Release)!

1. Navigate to GitHub tags/releases page
2. Create a new release
3. `cd` to `build-scripts/mac` (or `.../win`) and run `./run_pyinstaller.sh`
4. (Mac only) run `./maketar.sh`
   - This is done since executables only retain their `chmod +x` status when using tarballs
5. Upload `.tgz`/`.exe` (*NOT* raw Unix executable!) as attachments to the release

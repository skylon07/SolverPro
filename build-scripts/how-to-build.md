# How to Build (and Release)!

1. Update `getVersion()` string
2. `cd` to `build-scripts/mac` (or `.../win`) and run `./run_pyinstaller.sh`
3. (Mac only) run `./maketar.sh`
   - This is done since executables only retain their `chmod +x` status when using tarballs
4. Navigate to GitHub tags/releases page
5. Create a new release
6. Upload `.tgz`/`.exe` (*NOT* raw Unix executable!) as attachments to the release

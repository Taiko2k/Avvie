
<img src="https://user-images.githubusercontent.com/17271572/65824200-63a78800-e2c1-11e9-84c9-d2ad8cc97526.png" align="left" height="157px" hspace="0px" vspace="20px">

## Avvie!

A utility for quickly cropping images. Designed to be faster than the time it takes to locate the crop tool in GIMP.
<br><br>

## Features

<img src="https://user-images.githubusercontent.com/17271572/152432007-e158b870-da70-4bf5-b47f-718a87d49484.png" hspace="0px" vspace="0px" height="300px" align="right">

 - Quickly crop square images for avatars
 - Crop desktop wallpapers from photos
 - Scale images to preset output sizes
 - Quick saving
 - And more handy features

<br><br><br><br>

## Usage tips

 - You can import by drag and drop from your Pictures folder
 - Hold <kbd>Shift</kbd> to move the selection rectangle slowly
 - Tap <kbd>Ctrl</kbd> to enter free rectangle mode
 - Click the preview to toggle between ***square*** and ***circle*** (The final output will always be square)
 - You can type a custom ratio into the entry field next to the "Custom" option e.g. `4:3`, then press Enter.
 - You can also type a custom crop resolution into that same field, e.g. `300,500`.
 - **[Permission workaround]** Run `sudo flatpak override com.github.taiko2k.avvie --filesystem=host` to allow drag and drop from all file locations.

## Install
Flatpak is the recommended way to install Avvie. You can get the latest version from flathub by clicking the button below.

<a href='https://flathub.org/apps/details/com.github.taiko2k.avvie'><img width='240' alt='Download on Flathub' src='https://flathub.org/assets/badges/flathub-badge-i-en.png'/></a>

### Third Party Packages
You may also be able to obtain Avvie from your distribution's package manager. Note these packages are maintained independently and thus may differ from the official version on Flathub. Please report any issues experienced to the package maintainer.

[![Packaging status](https://repology.org/badge/vertical-allrepos/avvie.svg)](https://repology.org/project/avvie/versions)

## Build from source
The easiest way to build is by cloning this repo with GNOME Builder. It will automatically resolve all relevant flatpak SDKs automatically. You can then export the bundle if you wish.

Alternatively, clone the repo and use the following commands to build with meson.
```
meson builddir --prefix=/usr/local
sudo ninja -C builddir install
```

To build a flatpak from the command line, use the following commands.
```
flatpak-builder --user --install flatpak-builddir com.github.taiko2k.avvie.json
flatpak run com.github.taiko2k.avvie
```

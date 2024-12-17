Get-ChildItem *.png | ForEach-Object {
    # Step 1: Set background to black and remove alpha
    magick $_.FullName -background black -alpha remove ($_.BaseName + "_whitebg.png")

    # Step 2: Negate the colors
    magick ($_.BaseName + "_whitebg.png") -negate ($_.BaseName + "_inverted.png")

    # Step 3: Convert negated image to PNM
    magick ($_.BaseName + "_inverted.png") ($_.BaseName + ".pnm")

    # Step 4: Convert PNM to SVG using Potrace
    potrace ($_.BaseName + ".pnm") -s -o ($_.BaseName + ".svg")

    # Step 5: Remove unwanted fill attribute
    (Get-Content ($_.BaseName + ".svg")) -replace '\nfill="#000000"', '' | Set-Content ($_.BaseName + ".svg")
}
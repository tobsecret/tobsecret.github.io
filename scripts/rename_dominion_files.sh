for f in $(find . -name "200px-*"); do
  new_name="${f/200px-/}"
  
  echo "Renaming $f to $new_name"
  mv "$f" "$new_name"
done
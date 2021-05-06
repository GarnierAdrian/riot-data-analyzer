for f in data/cache/game_files/*.json
do
echo "Processing $f file...";
mongoimport --file $f -d leagueRadar -c game;
done

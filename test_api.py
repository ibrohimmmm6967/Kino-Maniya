from db_api import *

print("🎬 Movie:", get_movie_by_code("123"))
print("🔍 Search:", search_movies_by_name("a"))
print("🎭 Genre:", get_movies_by_genre("Fantastika"))
print("🔥 Top:", get_top_movies())
print("📊 Count:", count_movies())
print("👁 Views:", sum_views())

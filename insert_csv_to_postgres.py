import os

import pandas as pd
import psycopg2
from psycopg2 import sql

from config import MODEL_PATH

# Connect to the database
conn = psycopg2.connect(
    dbname="Book-Recom",
    user="postgres",
    password="admin",
    host="localhost",
)
# ====== READ BOOKS
# # Read CSV into a DataFrame
# df = pd.read_csv(os.path.join(MODEL_PATH, 'df_books_processed.csv.gz'),)
# print("csv was read")
#
# # Iterate over DataFrame rows as (index, Series) pairs.
# for index, row in df.iterrows():
#     # Build SQL query and data tuple
#     print(row)
#     query = """INSERT INTO books(book_id, title_without_series, description, publication_year, publisher, ratings_count, average_rating, image_url, url, is_ebook, num_pages, mod_title)
#                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
#     data = (row['book_id'], row['title_without_series'], row['description'], row['publication_year'], row['publisher'],
#             row['ratings_count'], row['average_rating'], row['image_url'], row['url'], row['is_ebook'],
#             row['num_pages'], row['mod_title'])
#
#     # Execute the query
#     cursor = conn.cursor()
#     cursor.execute(query, data)
#     conn.commit()

# ====== READ USERS REVIEWS
# print("reading...")
# df = pd.read_csv(os.path.join(MODEL_PATH, 'df_books_reviews_processed.csv.gz'),)
# print("csv was read")
#
# # Iterate over DataFrame rows as (index, Series) pairs.
# for index, row in df.iterrows():
#     # Build SQL query and data tuple
#     print(row)
#     insert_query = sql.SQL(
#         "INSERT INTO book_reviews (book_id, title_without_series, description, publication_year, publisher, ratings_count, average_rating, image_url, url, is_ebook, num_pages, mod_title, user_id, review_text, rating, book_id_mapped, publisher_mapped, is_ebook_mapped, user_id_mapped) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
#     )
#     data = (row['book_id'], row['title_without_series'], row['description'], row['publication_year'], row['publisher'],
#          row['ratings_count'], row['average_rating'], row['image_url'], row['url'], row['is_ebook'], row['num_pages'],
#          row['mod_title'], row['user_id'], row['review_text'], row['rating'], row['book_id_mapped'],
#          row['publisher_mapped'], row['is_ebook_mapped'], row['user_id_mapped'])
#
#     # Execute the query
#     cursor = conn.cursor()
#     cursor.execute(insert_query, data)
#     conn.commit()

# ======= READ REVIEWS EXTENDED
# print("reading...")
# df = pd.read_csv(os.path.join(MODEL_PATH, 'df_final_review.csv.gz'),)
# print("csv was read")
#
# # Iterate over DataFrame rows as (index, Series) pairs.
# for index, row in df.iterrows():
#     # Build SQL query and data tuple
#     print(row)
#     insert_query = sql.SQL(
#         "INSERT INTO book_reviews_extended (book_id, list_review_text, combined_processed_review, preprocessed_reviews) VALUES (%s, %s, %s, %s)"
#     )
#
#     data = (row['book_id'], row['list_review_text'], row['combined_processed_review'], row['preprocessed_reviews'])
#
#     # Execute the query
#     cursor = conn.cursor()
#     cursor.execute(insert_query, data)
#     conn.commit()

# Close the cursor and connection
cursor.close()
conn.close()

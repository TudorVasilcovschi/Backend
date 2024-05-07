import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pickle import dump

import numpy as np
import pandas as pd
from scipy.sparse import hstack, coo_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Reader, Dataset
from surprise import model_selection

from config import MODEL_PATH
from data_loader import load_pickle_file, load_csv_file
from database.database import Database


def load_books_data():
    print("loading books...")
    conn = Database.get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM books")
                books = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                print("finished loading books!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            Database.return_connection(conn)
            return books
    else:
        print("No database connection.")


def load_reviews_data():
    print("loading book reviews...")
    conn = Database.get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DISTINCT * FROM book_reviews")
                book_reviews = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                print("finished loading book reviews!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            Database.return_connection(conn)
            return book_reviews
    else:
        print("No database connection.")


def load_extended_reviews_data():
    print("loading extended reviews...")
    conn = Database.get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM book_reviews_extended")
                extended_reviews = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                print("finished loading extended reviews!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            Database.return_connection(conn)
            return extended_reviews
    else:
        print("No database connection.")


class Recommender:
    paths = {
        # common
        'final_review': os.path.join(MODEL_PATH, 'df_final_review.csv.gz'),
        'tfidf_description': os.path.join(MODEL_PATH, 'tfidf_description.pkl'),
        'vectorizer_description': os.path.join(MODEL_PATH, 'vectorizer_description.pkl'),
        # this is for first cut system
        'vectorizer_title_fc': os.path.join(MODEL_PATH, 'vectorizer_title.pkl'),
        # 'vectorizer_review_fc': os.path.join(MODEL_PATH, 'vectorizer_review_similarity.pkl'),
        'tfidf_review_fc': os.path.join(MODEL_PATH, 'tfidf_review_similarity.pkl'),
        'tfidf_title_fc': os.path.join(MODEL_PATH, 'tfidf_title.pkl'),
        # this is for content recommendation
        'vectorizer_title': os.path.join(MODEL_PATH, 'vectorizer_title_content.pkl'),
        'vectorizer_review': os.path.join(MODEL_PATH, 'vectorizer_review_content.pkl'),
        # 'tfidf_review': os.path.join(MODEL_PATH, 'tfidf_review_content.pkl'),
        # 'tfidf_title': os.path.join(MODEL_PATH, 'tfidf_title_content.pkl'),

        'le1': os.path.join(MODEL_PATH, 'le1.pkl'),
        'le4': os.path.join(MODEL_PATH, 'le4.pkl'),
        'le7': os.path.join(MODEL_PATH, 'le7.pkl'),
        'le9': os.path.join(MODEL_PATH, 'le9.pkl'),
        'norm': os.path.join(MODEL_PATH, 'norm.pkl'),
        'clf_lr': os.path.join(MODEL_PATH, 'clf_lr.pkl'),
        'model_svd': os.path.join(MODEL_PATH, 'model_svd.pkl')
    }

    _instance = None

    # singleton
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Recommender, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        self.df_books_reviews_processed = None
        self.df_books_processed = None
        self.df_final_review = None
        self.le1 = None
        self.le4 = None
        self.le7 = None
        self.le9 = None
        self.vectorizer_description = None
        self.vectorizer_review = None
        self.vectorizer_title_fc = None
        self.vectorizer_title = None
        self.tfidf_description = None
        self.tfidf_review_fc = None
        self.tfidf_title_fc = None
        self.norm = None
        self.clf_lr = None
        self.model_svd = None
        self.load_data()

    def load_data(self):
        logging.info("Loading data ...")
        start_time = time.time()


        with ThreadPoolExecutor(max_workers=3) as executor:
            future_books = executor.submit(load_books_data)
            future_reviews = executor.submit(load_reviews_data)
            future_extended_reviews = executor.submit(load_extended_reviews_data)
            try:
                self.df_books_processed = future_books.result()
                self.df_books_reviews_processed = future_reviews.result()
                self.df_final_review = future_extended_reviews.result()

            except Exception as e:
                print(f"An exception occurred: {e}")

        self.le1, self.le4, self.le7, self.le9 = [load_pickle_file(self.paths[key]) for key in
                                                  ['le1', 'le4', 'le7', 'le9']]
        self.vectorizer_description = load_pickle_file(self.paths['vectorizer_description'])
        self.vectorizer_review = load_pickle_file(self.paths['vectorizer_review'])
        self.vectorizer_title_fc = load_pickle_file(self.paths['vectorizer_title_fc'])
        self.vectorizer_title = load_pickle_file(self.paths['vectorizer_title'])
        self.tfidf_description = load_pickle_file(self.paths['tfidf_description'])
        self.tfidf_review_fc = load_pickle_file(self.paths['tfidf_review_fc'])
        self.tfidf_title_fc = load_pickle_file(self.paths['tfidf_title_fc'])
        self.norm = load_pickle_file(self.paths['norm'])
        self.clf_lr = load_pickle_file(self.paths['clf_lr'])
        self.model_svd = load_pickle_file(self.paths['model_svd'])

        end_time = time.time()
        logging.info(f'Finished data loading. Time taken: {end_time - start_time} seconds')
        print("done loading")

    # ======== Cold Start ========
    def top_book_average_rating(self):
        top50_highest_rated_books = self.df_books_processed[(self.df_books_processed['average_rating'] >= 4.50) & (
                self.df_books_processed['ratings_count'] > 3000.0)].sort_values(by='average_rating', ascending=False)
        return top50_highest_rated_books[
            ['book_id', 'title_without_series', 'average_rating', 'image_url', 'url']].head(10)

    def top_short_books(self):
        top_50_short_books = self.df_books_processed[
            (self.df_books_processed['num_pages'] <= 300) & (self.df_books_processed['ratings_count'] > 3000.0) & (
                    self.df_books_processed['average_rating'] >= 4.50)].sort_values(by='average_rating',
                                                                                    ascending=False)

        return top_50_short_books[
            ['book_id', 'title_without_series', 'num_pages', 'average_rating', 'image_url', 'url']].head(
            10)

    def top_paper_books(self):
        df_ebook = self.df_books_processed[
            (self.df_books_processed['average_rating'] >= 4.5) & (
                        self.df_books_processed['ratings_count'] > 3000.0)].sort_values(
            by='average_rating', ascending=False)
        top_50_paper_books = df_ebook[df_ebook['is_ebook'] == False]
        return top_50_paper_books[['book_id', 'title_without_series', 'num_pages', 'average_rating', 'image_url', 'url']].head(10)

    def top_e_books(self):
        df_ebook = self.df_books_processed[
            (self.df_books_processed['average_rating'] >= 4.5) & (
                        self.df_books_processed['ratings_count'] > 3000.0)].sort_values(
            by='average_rating', ascending=False)
        top_50_e_books = df_ebook[df_ebook['is_ebook'] == True]
        return top_50_e_books[['book_id', 'title_without_series', 'num_pages', 'average_rating', 'image_url', 'url']].head(10)

    # ======== Recommendations based on input ========
    def top_similar_title_books(self, title):
        title = str(title)
        title = re.sub("[^a-zA-Z0-9 ]", "", title.lower())

        try:
            query_vec = self.vectorizer_title_fc.transform([title])
            similarity = cosine_similarity(query_vec, self.tfidf_title_fc).flatten()
            indices = np.argpartition(similarity, -50)[-50:]
            results = self.df_books_processed.iloc[indices]
            return results[['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages']].head(10)
        except Exception as _:
            raise

    def top_similar_description_books(self, description):
        description = str(description)
        description = re.sub("[^a-zA-Z0-9 ]", "", description.lower())

        try:
            query_vec = self.vectorizer_description.transform([description])
            similarity = cosine_similarity(query_vec, self.tfidf_description).flatten()
            indices = np.argpartition(similarity, -50)[-50:]
            results = self.df_books_processed.iloc[indices]
            return results[['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages']].head(10)
        except Exception as _:
            raise

    def top_similar_reviews_books(self, book_id):
        try:
            # Fetch index positions for the specific book_id
            index_positions = self.df_final_review[self.df_final_review['book_id'] == book_id].index
            if index_positions.empty:  # Ensure there are reviews for the book
                print("No reviews found for the given book_id")
                return pd.DataFrame()  # Return an empty DataFrame if no reviews found

            # Calculate the cosine similarity
            similarity_scores = cosine_similarity(self.tfidf_review_fc[index_positions], self.tfidf_review_fc).flatten()

            # Find top indices directly from the DataFrame's index rather than positional indices
            if len(similarity_scores) > 0:
                indices = np.argpartition(similarity_scores, -50)[-50:]
                book_ids = set(self.df_final_review.iloc[indices]['book_id'])
                score = [(score, book) for score, book in enumerate(book_ids)]
                df_score = pd.DataFrame(score, columns=['score', 'book_id'])
                results = (self.df_books_processed[self.df_books_processed['book_id'].isin(book_ids)].merge(df_score,
                                                                                                  on='book_id')).sort_values(by='score')

                return results[
                    ['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url',
                     'url', 'num_pages']]
            else:
                print("No similarity scores computed.")
                return pd.DataFrame()
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

    def similar_user_df(self, user_id):
        try:
            df_liked_books = self.df_books_reviews_processed[self.df_books_reviews_processed['user_id'] == user_id]
            liked_books = set(df_liked_books['book_id'])
            top_5_liked_books = df_liked_books.sort_values(by='rating', ascending=False)['book_id'][:5]
            similar_user = \
                self.df_books_reviews_processed[
                    (self.df_books_reviews_processed['book_id'].isin(top_5_liked_books)) & (self.df_books_reviews_processed['rating'] > 4)][
                    'user_id']
            data = self.df_books_reviews_processed[(self.df_books_reviews_processed['user_id'].isin(similar_user))][
                ['user_id', 'book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages', 'ratings_count']]
            return data, liked_books
        except Exception as _:
            raise

    def top_users_choice_books(self, recs, liked_books):
        try:
            all_recs = recs["book_id"].value_counts()
            all_recs = all_recs.to_frame().reset_index()
            all_recs.columns = ["book_id", "book_count"]
            all_recs = all_recs.merge(recs, how="inner", on="book_id")
            all_recs["score"] = all_recs["book_count"] * (all_recs["book_count"] / all_recs["ratings_count"])
            popular_recs = all_recs.sort_values("score", ascending=False)
            popular_recs_unbiased = popular_recs[~popular_recs["book_id"].isin(liked_books)].drop_duplicates(
                subset=['title_without_series'])
            return popular_recs_unbiased[
                ['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages']].head(10)
        except Exception as _:
            raise

    # ======== Content Filtering ========
    def content_recommendation(self, user_id):
        books_reviewed_by_user = set(
            self.df_books_reviews_processed[self.df_books_reviews_processed['user_id'] == user_id]['book_id'])
        user_books = self.df_books_processed[
            (~self.df_books_processed['book_id'].isin(list(books_reviewed_by_user)))].merge(self.df_final_review,
                                                                                            on='book_id')
        user_books['user_id'] = len(user_books) * [user_id]
        user_books.reset_index(drop=True, inplace=True)
        user_books['book_id'] = user_books['book_id'].astype(str)  # Convert book_id to string for comparison
        user_books = user_books[user_books['book_id'].isin(self.le1.classes_)]
        user_books['book_id_mapped'] = self.le1.transform(user_books['book_id'])
        user_books['publisher_mapped'] = self.le4.transform(user_books['publisher'])
        user_books['is_ebook_mapped'] = self.le7.transform(user_books['is_ebook'])
        user_books['user_id_mapped'] = self.le9.transform(user_books['user_id'])
        user_books['combined_processed_review'].fillna("", inplace=True)
        tfidf_title = self.vectorizer_title.transform(user_books['mod_title'])
        tfidf_review = self.vectorizer_review.transform(user_books['combined_processed_review'])
        user_book_numeric = user_books[
            ['book_id_mapped', 'publisher_mapped', 'is_ebook_mapped',  'user_id_mapped',
             'publication_year', 'ratings_count', 'average_rating', 'num_pages']]
        data_scaled = self.norm.transform(user_book_numeric)
        data_scaled = hstack((data_scaled, tfidf_title, tfidf_review), dtype=np.float32)

        prediction = self.clf_lr.predict(data_scaled.tocsr())
        user_books['rating'] = prediction

        top_50_books_for_user_content = user_books.sort_values(by=['rating'], ascending=False)[:50]
        return top_50_books_for_user_content[
            ['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages']].head(10)

    # ======== Collaborative Filtering ========
    def similar_users(self, user_id):
        # ia cartile apreciate the utilizator
        books_liked_by_user = set(
            self.df_books_reviews_processed[self.df_books_reviews_processed['user_id'] == user_id]['book_id'])
        # ia numarul cartilor comune apreciate pentru fiecare utilizator
        count_other_similar_users = \
            self.df_books_reviews_processed[self.df_books_reviews_processed['book_id'].isin(books_liked_by_user)][
                'user_id'].value_counts()
        df_similar_user = count_other_similar_users.to_frame().reset_index()
        df_similar_user.columns = ['user_id', 'matching_book_count']  # doar coloanele astea ne intereseaza

        # se selecteaza doar 1% din ei (adica cei mai asemanatori)
        top_onepercent_similar_users = df_similar_user[
            df_similar_user['matching_book_count'] >= np.percentile(df_similar_user['matching_book_count'], 99)]
        top_users = set(top_onepercent_similar_users['user_id'])

        # construieste matricea une randul = utilizator, coloana = carte, celula = raitng-ul
        df_similar_user = self.df_books_reviews_processed[(self.df_books_reviews_processed['user_id'].isin(top_users))][
            ['user_id_mapped', 'book_id_mapped', 'rating', 'user_id', 'book_id', 'title_without_series',
             'ratings_count', 'image_url', 'url', 'average_rating']]
        ratings_mat_coo = coo_matrix(
            (df_similar_user["rating"], (df_similar_user["user_id_mapped"], df_similar_user["book_id_mapped"])))
        ratings_mat = ratings_mat_coo.tocsr()

        # calculeaza similaritatea dintre utilizatorul introdus si toti ceilalti
        my_index = list(self.le9.transform([user_id]))[0]
        similarity = cosine_similarity(ratings_mat[my_index, :], ratings_mat).flatten()
        # ia primii 50 cei mai asemanatori
        similar_users_index = np.argsort(similarity)[-1:-51:-1]
        # filtreaza recomandarilor astfel incat sa excluda cartile deja apreciate de utilizator
        df_similar_users_refined = df_similar_user[(df_similar_user["user_id_mapped"].isin(similar_users_index)) & (
            ~df_similar_user['book_id'].isin(books_liked_by_user))].copy()
        return df_similar_users_refined

    def user_similarity_recommendation(self, df_similar_users_refined):
        # numără recomandările pentru fiecare carte în funcție de evaluările utilizatorilor similari.
        all_recs = df_similar_users_refined['book_id'].value_counts()
        all_recs = all_recs.to_frame().reset_index()
        all_recs.columns = ["book_id", "book_count"]
        all_recs_book_id = list(all_recs['book_id'])

        # Se calculează un scor pentru fiecare carte, ținând cont de numărul de recomandări și popularitatea cărții
        all_recs_new = self.df_books_processed[self.df_books_processed['book_id'].isin(all_recs_book_id)]
        all_recs_new = all_recs_new.merge(all_recs, on='book_id', how='inner')
        all_recs_new['score'] = all_recs_new['book_count'] * (
                all_recs_new['book_count'] / all_recs_new['ratings_count'])
        return all_recs_new.sort_values(by='score', ascending=False)[
            ['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages']].head(10)

    def item_similarity_recommendation(self, book_id):
        # utilizatorii care au apreciat cartea
        users_who_liked_book = set(
            self.df_books_reviews_processed[self.df_books_reviews_processed['book_id'] == book_id]['user_id'])

        # evaluările altor cărți ale utilizatorilor care au apreciat cartea data
        books_id_remaining = self.df_books_reviews_processed[
            (self.df_books_reviews_processed['user_id'].isin(list(users_who_liked_book)))]

        # matrice de evaluări unde rândurile reprezintă cărțile și coloanele reprezintă utilizatorii.
        ratings_mat_coo = coo_matrix((books_id_remaining["rating"],
                                      (books_id_remaining["book_id_mapped"], books_id_remaining["user_id_mapped"])))
        ratings_mat = ratings_mat_coo.tocsr()
        my_index = list(self.le1.transform([book_id]))[0]

        # similaritatea cosinus între cartea dată și toate celelalte cărți
        similarity = cosine_similarity(ratings_mat[my_index, :], ratings_mat).flatten()
        # Se identifică indexurile celor mai similare 50 de cărți
        similar_books_index = np.argsort(similarity)[-1:-51:-1]
        # scor de similaritate
        score = [(score, book) for score, book in enumerate(similar_books_index)]
        df_score = pd.DataFrame(score, columns=['score', 'book_id_mapped'])

        # Se combină datele din df_books_users_processed cu df_score pentru a obține ID-urile cărților și scorurile lor.
        df_similar_books_to_recommend = (self.df_books_reviews_processed[(
            self.df_books_reviews_processed['book_id_mapped'].isin(list(similar_books_index)))].merge(df_score,
                                                                                                      on='book_id_mapped'))[
            ['book_id', 'score']]
        # se elimina duplicatele
        unique_df_similar_books_to_recommend = df_similar_books_to_recommend.drop_duplicates(keep='first')
        # Se combină df_books_processed cu unique_df_similar_books_to_recommend pentru a obține toate detaliile cărților recomandate.
        final_books = (self.df_books_processed[self.df_books_processed['book_id'].isin(
            set(unique_df_similar_books_to_recommend['book_id'].values))].merge(unique_df_similar_books_to_recommend,
                                                                                on='book_id')).sort_values(by='score')
        return final_books[['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages']].head(10)

    def svd_recommendation(self, user_id):
        book_id = set(self.df_books_reviews_processed[self.df_books_reviews_processed['user_id'] == user_id]['book_id'])
        user_books = self.df_books_processed[~self.df_books_processed['book_id'].isin(book_id)].copy()
        user_books['user_id'] = len(user_books) * [user_id]
        user_books.reset_index(drop=True, inplace=True)
        user_books['rating'] = 0
        reader = Reader(rating_scale=(0, 5))
        df_svd_predict = Dataset.load_from_df(user_books[['user_id', 'book_id', 'rating']], reader)
        NA, test = model_selection.train_test_split(df_svd_predict, test_size=1.0)
        predictions = self.model_svd.test(test)
        predictions = [prediction.est for prediction in predictions]
        user_books['rating_svd'] = predictions
        top_50_books_for_user_content = user_books.sort_values(by=['rating_svd'], ascending=False)[:50]

        return top_50_books_for_user_content[
            ['book_id', 'title_without_series', 'publication_year', 'publisher', 'average_rating', 'image_url', 'url', 'num_pages']].head(10)

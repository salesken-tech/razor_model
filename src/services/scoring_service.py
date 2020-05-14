import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import pandas as pd

from src.services import text_service, signal_service
from src.utilities import sken_singleton, sken_logger, db
from src.utilities.objects import VadChunk, Match

logger = sken_logger.get_logger("scoring_service")


def vad_chunk_match(vad_chunk, product_id):
    tokens = text_service.make_root_word(text_service.get_tokens(vad_chunk.text))
    if len(tokens) > 0:
        logger.info("Made {} token for snippet = {}".format(len(tokens), vad_chunk.sid))
        signals = sken_singleton.Singletons.get_instance().get_cached_signals()[str(product_id)]

        def get_signal_scoring(signal):
            signal_df = signal.token_df
            threshold = signal.threshold
            matched = []
            matched_vals = []
            score = 0
            for tok in tokens:
                for i, val in enumerate(signal_df.val):
                    if val.isin([tok]).any() and tok not in matched_vals:
                        matched_vals.extend(val.values.tolist())
                        matched.append(tok)
                        score += signal_df.score[i]
            if score >= threshold:
                return Match(vad_chunk.sid, signal.sid, vad_chunk.text, signal.value, matched, score, threshold,
                             vad_chunk,
                             signal)
            else:
                return 0

        with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 2) as executor:
            future = list(executor.map(get_signal_scoring, signals))
        final_result = []
        for item in future:
            if item != 0:
                final_result.append(item)
        return final_result
    else:
        logger.info("No token found for snippet={}".format(vad_chunk.sid))


def lq_detection_task(prod_id, task_id):
    sql = "select id,from_time,to_time,text_,speaker,task_id from snippet  where task_id=%s"
    rows, col_names = db.DBUtils.get_instance().execute_query(sql, (task_id,), is_write=False, is_return=True)
    vad_chunks = []
    if len(rows) != 0:
        logger.info("Found {} snippets for task_id={}".format(len(rows), task_id))
        for row in rows:
            vad_chunks.append(
                VadChunk(row[col_names.index("id")], row[col_names.index("from_time")], row[col_names.index("to_time")],
                         row[col_names.index("speaker")], row[col_names.index("text_")],
                         row[col_names.index("task_id")], old_snippet_list=None,
                         questions=None))
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count() - 1) as exe:
            future = list(exe.map(vad_chunk_match, vad_chunks, [prod_id] * len(vad_chunks)))
        result = {}
        for item in future:
            if len(item) > 0:
                if str(item[0].snippet_id) not in result.keys():
                    result[str(item[0].snippet_id)] = {"input_sentence": item[0].snippet_text,
                                                       "signal": item[0].signal_text,
                                                       "tokens": item[0].matched_tokens,
                                                       "score": str(item[0].score), "threshold": str(item[0].threshold),
                                                       "id": item[0].signal_id,
                                                       "html_": ""}
                else:
                    if item[0].score >= result[str(item[0].snippet_id)].score:
                        result[str(item[0].str(item[0].snippet_id))] = {"input_sentence": item[0].snippet_text,
                                                                        "signal": item[0].signal_text,
                                                                        "tokens": item[0].matched_tokens,
                                                                        "score": str(item[0].score),
                                                                        "threshold": str(item[0].threshold),
                                                                        "id": item[0].signal_id,
                                                                        "html_": ""}
        final_result = list(result.values())
        snippet_ids = list(result.keys())
        print(final_result)
        print(snippet_ids)
        if len(final_result) > 0:
            for sid, item in zip(snippet_ids, final_result):
                sql = "INSERT INTO public.signal_caught (snippet_id, signal_generated_id, score, match_method) " \
                      "VALUES(%s, " \
                      "(select signal_generated.id from signal_generated where signal_generated.signal_id=%s), %s, " \
                      "'RAZOR'); "
                db.DBUtils.get_instance().execute_query(sql, (sid, item["id"], item["score"]), is_write=True,
                                                        is_return=False)
        logger.info("Found {} matches for {} snippets ".format(len(final_result), len(vad_chunks)))
        return final_result

    else:
        return "no snippets found"


def lq_detection_file(prod_id, file_path):
    s = time.time()
    if str(prod_id) not in sken_singleton.Singletons.get_instance().get_cached_signals().keys():
        signal_service.make_cached_signals_product(prod_id)
    df = pd.read_excel(file_path)
    vad_chunks = []
    if len(df) != 0:
        logger.info("Got {} sentences in file {}".format(len(df), file_path))
        for i, val in enumerate(df.text_):
            vad_chunks.append(
                VadChunk(df.id[i], None, None,
                         None, val,
                         None, old_snippet_list=None,
                         questions=None))
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count() - 1) as exe:
            future = list(exe.map(vad_chunk_match, vad_chunks, [str(prod_id)] * len(vad_chunks)))
        final_result = []
        for item1 in future:
            if len(item1) > 0:
                for item in item1:
                    final_result.append(
                        {"input_sentence": item.snippet_text, "signal": item.signal_text, "tokens": item.matched_tokens,
                         "score": item.score, "threshold": item.threshold, "id": item.signal_id})
        new_df = pd.DataFrame(final_result)
        logger.info("Found {} matches for {} snippets ".format(len(final_result), len(vad_chunks)))
        logger.info(
            "Time taken for matching {}X{} sentence={}".format(
                len(sken_singleton.Singletons.get_instance().get_cached_signals()[prod_id]),
                len(vad_chunks), time.time() - s))
        new_df.to_excel("/home/andy/Desktop/test_data_result.xlsx")
        return final_result

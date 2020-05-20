from src.utilities import constants, db, sken_logger, sken_singleton, sken_exceptions
from src.utilities.objects import Signal
import pandas as pd
import os
import pickle
from src.services.text_service import make_root_word

logger = sken_logger.get_logger('signal_service')


def make_product_signal(signal_tokens, scores, threshold, value, product_id):
    signal_token_lists = []
    logger.info("Making signal_df")
    for token, score in zip(signal_tokens, scores):
        signal_token_lists.append({'val': pd.Series(make_root_word(signal_tokens[token])), 'score': int(score)})

    df = pd.DataFrame(signal_token_lists)
    pickel_string = pickle.dumps(df)
    sql = "insert into public.product_signal (name, color, value, product_id, created_at, updated_at, is_active, " \
          "type, engine, match_type, do_generate) values(%s, '#f09600', %s, %s, now(), now(), true, '', " \
          "'RAZOR'" \
          ", 'BOTH', false) returning id; "

    rows, col_names = db.DBUtils.get_instance().execute_query(sql, (
        constants.fetch_constant("signal_name"), value, product_id), is_write=True,
                                                              is_return=True)
    sql = "INSERT INTO public.signal_generated (signal_id, text_, created_at, snippets_id, is_active) VALUES(%s, %s, " \
          "now(), NULL, false); "
    db.DBUtils.get_instance().execute_query(sql, (rows[0][col_names.index("id")], value), is_write=True,
                                            is_return=False)
    sql = "INSERT INTO public.product_signal_file (product_signal_id, signal_file, threshold) VALUES(%s, %s, %s); "
    db.DBUtils.get_instance().execute_query(sql, (rows[0][col_names.index("id")], pickel_string, threshold),
                                            is_write=True,
                                            is_return=False)
    logger.info("Made signal entry in db")


def delete_product_signal(signal_id):
    sql = "delete from signal_generated where signal_id=%s"
    db.DBUtils.get_instance().execute_query(sql, (signal_id,), is_write=True, is_return=False)
    sql = """DELETE FROM public.product_signal WHERE id=%s"""
    db.DBUtils.get_instance().execute_query(sql, (signal_id,), is_write=True, is_return=False)
    return True


def make_cached_signals_product(task_id):
    # sql = "select pipeline_product.product_id from pipeline_product where pipeline_product.pipeline_id in( select " \
    #       "pipeline.id from pipeline where pipeline.organization_id in ( select org_user.organizationid from org_user " \
    #       "where org_user.userid = ( select task.actor from task where task.id = %s))) "
    sql = "select product_id from lead  where lead.id =(select task.lead_id from task where task.id=%s)"
    rows, col_names = db.DBUtils.get_instance().execute_query(sql, (task_id,), is_write=False, is_return=True)
    if len(rows) > 0:
        product_id = rows[0][col_names.index("product_id")]
    else:
        raise sken_exceptions.NoProductFound(task_id)
    if str(product_id) not in sken_singleton.Singletons.get_instance().get_cached_signals().keys():
        logger.info("Did not find the signals for the product_id={} in cache".format(product_id))
        sql = "select product_signal.id, product_signal.value, product_signal_file.signal_file as file_path, " \
              "product_signal_file.threshold from product_signal left join product_signal_file on product_signal.id = " \
              "product_signal_file.product_signal_id where product_id = %s and engine = 'RAZOR' "
        rows, col_names = db.DBUtils.get_instance().execute_query(sql, (product_id,), is_write=False, is_return=True)
        if len(rows) != 0:
            logger.info("Caching {} Signals  for product={}".format(len(rows), product_id))
            signals = []
            for row in rows:
                signal = Signal(row[col_names.index("id")], row[col_names.index("threshold")],
                                pickle.loads(row[col_names.index("file_path")]), row[col_names.index("value")],
                                "")
                signals.append(signal)
            sken_singleton.Singletons.get_instance().set_cached_signals(product_id, signals)
            return product_id
        else:
            raise sken_exceptions.NoSignalFound(product_id, task_id)

    else:
        logger.info("Skipping caching as the signal for {} product_id are already present in RAM".format(product_id))
        return product_id

"""Internal function-only PostgreSQL adapter. Supply a fresh DB-API connection.

No driver, credentials or authentication is selected here. Context ownership must
come from a verified server session, never a field in a desktop submission.
"""
import json


class RepositoryError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


FUNCTIONS = {
    'submit_text': 10, 'claim_text_job': 0, 'read_job_original': 2,
    'renew_text_job': 2, 'fail_text_job': 3, 'stage_text': 5,
    'stage_vectors': 6, 'publish_text': 2,
    'completed_passages': 2,
}


class PostgresRepository:
    def __init__(self, connect):
        self.connect = connect

    def call(self, function, *args):
        if function not in FUNCTIONS or len(args) != FUNCTIONS[function]:
            raise ValueError('unsupported_repository_operation')
        connection = None
        try:
            # Factory configures restricted role and verified session identity.
            # Each call has its own transaction/connection, including heartbeats.
            connection = self.connect()
            if connection.autocommit:
                raise ValueError('transaction_required')
            with connection.cursor() as cursor:
                cursor.execute("set local statement_timeout='5s'")
                cursor.execute("set local lock_timeout='3s'")
                params = tuple(json.dumps(a, allow_nan=False) if isinstance(a, (list, dict)) else a for a in args)
                cursor.execute(f"select gather_private.{function}({','.join(['%s']*len(args))})", params)
                result = cursor.fetchone()[0]
            connection.commit()
            return result
        except Exception as error:
            if connection is not None:
                try:
                    connection.rollback()
                except Exception:
                    pass
            state = getattr(error, 'sqlstate', None) or getattr(error, 'pgcode', None)
            code = 'stale_lease' if state == '55000' else (
                'invalid_input' if state and state[:2] in ('22', '23', '42') else 'temporarily_unavailable')
            raise RepositoryError(code) from None
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

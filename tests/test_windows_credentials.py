"""Windows-only integration, creates/deletes a unique TEST credential, no owner keys."""
import os
import unittest
import uuid
from jarvis.security import WindowsCredentials

@unittest.skipUnless(os.name == 'nt', 'Windows OS integration only')
class WindowsCredentialIntegration(unittest.TestCase):
    def test_test_credential_roundtrip_and_delete(self):
        # Never touch the app's actual provider targets or existing saved owner keys.
        target = 'JARVIS/ci-test/' + uuid.uuid4().hex
        class TestCredentials(WindowsCredentials):
            @staticmethod
            def target(provider):return target
        store=TestCredentials()
        try:
            self.assertIsNone(store.get('test'));self.assertFalse(store.status('test')['present'])
            store.set('test', 'synthetic-test-value-not-an-api-key')
            self.assertEqual(store.get('test'), 'synthetic-test-value-not-an-api-key')
            reopened=TestCredentials();self.assertEqual(reopened.get('test'),'synthetic-test-value-not-an-api-key');self.assertTrue(reopened.status('test')['present']);self.assertIsNotNone(reopened.status('test')['saved_at'])
            store.delete('test');self.assertIsNone(store.get('test'));self.assertFalse(store.status('test')['present'])
            store.delete('test')
        finally:store.delete('test')

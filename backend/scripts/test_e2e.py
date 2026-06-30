"""End-to-end test script for CLMS API.

Tests the full API flow via HTTP requests:
1. GET /health
2. GET /api/templates/docx
3. GET /api/templates/docx/{id}/html
4. POST /api/draft
5. POST /api/export/docx

Usage:
    python scripts/test_e2e.py [base_url]

Default base URL: http://localhost:8000
"""

import sys

import httpx


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    base_url = base_url.rstrip("/")

    passed = 0
    failed = 0
    total = 5

    print(f"Running E2E tests against: {base_url}\n")

    # Test 1: GET /health
    print("Test 1: GET /health")
    try:
        resp = httpx.get(f"{base_url}/health", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got {data.get('status')}"
        print("  PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}\n")
        failed += 1

    # Test 2: GET /api/templates/docx
    print("Test 2: GET /api/templates/docx")
    templates = []
    try:
        resp = httpx.get(f"{base_url}/api/templates/docx", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        templates = resp.json()
        assert isinstance(templates, list), f"Expected list, got {type(templates).__name__}"
        print(f"  Found {len(templates)} template(s)")
        print("  PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}\n")
        failed += 1

    # Test 3: GET /api/templates/docx/{first_id}/html
    print("Test 3: GET /api/templates/docx/{first_id}/html")
    html_content = ""
    try:
        assert len(templates) > 0, "No templates available from Test 2"
        first_id = templates[0].get("id") or templates[0].get("template_id")
        assert first_id, f"Could not extract template ID from: {templates[0]}"
        resp = httpx.get(f"{base_url}/api/templates/docx/{first_id}/html", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "html_content" in data, f"Response missing 'html_content' key: {list(data.keys())}"
        html_content = data["html_content"]
        print("  PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}\n")
        failed += 1

    # Test 4: POST /api/draft with sample variables
    print("Test 4: POST /api/draft")
    draft_html = ""
    try:
        payload = {
            "template_name": "KHS Material Ketenagalistrikan",
            "variables": {
                "nama_perusahaan": "PT Contoh Sejahtera",
                "tanggal_kontrak": "2025-01-01",
                "nilai_kontrak": "Rp 100.000.000",
            },
            "include_optional": True,
        }
        resp = httpx.post(f"{base_url}/api/draft", json=payload, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "html_content" in data, f"Response missing 'html_content' key: {list(data.keys())}"
        draft_html = data["html_content"]
        assert len(draft_html) > 0, "html_content is empty"
        print("  PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}\n")
        failed += 1

    # Test 5: POST /api/export/docx
    print("Test 5: POST /api/export/docx")
    try:
        export_html = draft_html or html_content or "<p>Test content</p>"
        payload = {
            "html_content": export_html,
            "format": "docx",
            "filename": "test_export",
        }
        resp = httpx.post(f"{base_url}/api/export/docx", json=payload, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        content = resp.content
        # Check PK signature (ZIP/DOCX magic bytes): PK\x03\x04
        assert content[:4] == b"PK\x03\x04", (
            f"Expected DOCX (PK signature), got first 4 bytes: {content[:4]!r}"
        )
        print(f"  Received {len(content)} bytes with valid PK signature")
        print("  PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}\n")
        failed += 1

    # Summary
    print("=" * 40)
    print(f"Results: {passed}/{total} passed")
    if failed > 0:
        print(f"         {failed}/{total} failed")
    print("=" * 40)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

#!/bin/bash
PGPASSWORD=dialflow psql -h 172.31.48.1 -U dialflow -d dialflow -c "SELECT table_name FROM information_schema.tables WHERE table_schema='test_tenant' ORDER BY table_name;"

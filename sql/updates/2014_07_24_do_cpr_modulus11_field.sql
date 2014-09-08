ALTER table os2webscanner_scanner ADD column "do_cpr_modulus11" boolean NOT NULL DEFAULT TRUE;
UPDATE os2webscanner_scanner SET do_cpr_modulus11 = FALSE;


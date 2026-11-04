ALTER TABLE `cbank_delta_ledger` ADD `charged_reads` integer DEFAULT 0 NOT NULL;--> statement-breakpoint
ALTER TABLE `cbank_delta_ledger` ADD `charged_writes` integer DEFAULT 0 NOT NULL;--> statement-breakpoint
ALTER TABLE `cbank_delta_ledger` ADD `prior_reads` integer DEFAULT 0 NOT NULL;--> statement-breakpoint
ALTER TABLE `cbank_delta_ledger` ADD `prior_writes` integer DEFAULT 0 NOT NULL;
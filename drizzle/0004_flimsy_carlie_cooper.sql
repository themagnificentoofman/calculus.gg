CREATE TABLE `cbank_delta_ledger` (
	`bundle_id` text PRIMARY KEY NOT NULL,
	`measured_reads` integer NOT NULL,
	`measured_writes` integer NOT NULL,
	`database_bytes` integer NOT NULL,
	`next_sequence` integer NOT NULL,
	`verified` integer NOT NULL,
	`activated` integer NOT NULL,
	`pending_id` text,
	`pending_hash` text,
	`halted` text,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `cbank_release_sources` (
	`release_id` text NOT NULL,
	`source_release_id` text NOT NULL,
	PRIMARY KEY(`release_id`, `source_release_id`)
);
--> statement-breakpoint
CREATE TABLE `cbank_selection_features` (
	`problem_ref` integer PRIMARY KEY NOT NULL,
	`idea` text NOT NULL,
	`structure` text NOT NULL,
	`technique` text NOT NULL,
	`combination` text NOT NULL,
	`weight` real NOT NULL
);
--> statement-breakpoint
CREATE TRIGGER cbank_features_immutable BEFORE UPDATE ON cbank_selection_features BEGIN SELECT RAISE(ABORT,'Create a new problem revision'); END;
--> statement-breakpoint
CREATE TRIGGER cbank_features_retained BEFORE DELETE ON cbank_selection_features BEGIN SELECT RAISE(ABORT,'Retain historical selection metadata'); END;
--> statement-breakpoint
CREATE TRIGGER cbank_sources_immutable BEFORE UPDATE ON cbank_release_sources BEGIN SELECT RAISE(ABORT,'Create a new release'); END;
--> statement-breakpoint
CREATE TRIGGER cbank_sources_retained BEFORE DELETE ON cbank_release_sources BEGIN SELECT RAISE(ABORT,'Retain historical release composition'); END;

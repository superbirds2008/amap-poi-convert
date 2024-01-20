package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
)

func get_location(address string, apiKey string) string {
	url := "https://restapi.amap.com/v3/geocode/geo"
	params := map[string]string{
		"address": address,
		"output":  "JSON",
		"key":     apiKey,
	}
	resp, err := http.Get(url + "?" + encodeParams(params))
	if err != nil {
		log.Fatalf("Error: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		// Parse the response and return the location
		// ...
	} else {
		log.Printf("Error: %v", resp.Status)
	}
	return ""
}

func get_pois(location string, apiKey string) []string {
	url := "https://restapi.amap.com/v3/geocode/regeo"
	params := map[string]string{
		"location":   location,
		"output":     "JSON",
		"key":        apiKey,
		"extensions": "all",
	}
	resp, err := http.Get(url + "?" + encodeParams(params))
	if err != nil {
		log.Fatalf("Error: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		// Parse the response and return the POIs
		// ...
	} else {
		log.Printf("Error: %v", resp.Status)
	}
	return nil
}

func process_csv(inputFile io.Reader, apiKey string, startLine int, endLine int) error {
	reader := csv.NewReader(inputFile)
	writer := csv.NewWriter(os.Stdout)

	// Skip lines before startLine
	for i := 0; i < startLine; i++ {
		_, err := reader.Read()
		if err != nil {
			return fmt.Errorf("error reading input file: %v", err)
		}
	}

	// Process lines between startLine and endLine
	for i := startLine; i < endLine; i++ {
		row, err := reader.Read()
		if err != nil {
			if err == io.EOF {
				break
			}
			return fmt.Errorf("error reading input file: %v", err)
		}

		address := row[0]
		location := get_location(address, apiKey)
		if location != "" {
			pois := get_pois(location, apiKey)
			for _, poi := range pois {
				writer.Write([]string{address, poi})
			}
		}
	}

	writer.Flush()
	if err := writer.Error(); err != nil {
		return fmt.Errorf("error writing output file: %v", err)
	}

	return nil
}

func main() {
	http.HandleFunc("/api/v1/process_csv", func(w http.ResponseWriter, r *http.Request) {
		file, _, err := r.FormFile("input_file")
		if err != nil {
			http.Error(w, "failed to read input file", http.StatusBadRequest)
			return
		}
		defer file.Close()

		err = process_csv(file, "e813774a4aea1a0b6ca95f16bcd36cd4", 0, 0)
		if err != nil {
			http.Error(w, fmt.Sprintf("failed to process CSV: %v", err), http.StatusInternalServerError)
			return
		}

		// Return the output file
		// ...
	})

	http.HandleFunc("/upload", func(w http.ResponseWriter, r *http.Request) {
		// Serve the HTML page for file upload
		// ...
	})

	log.Fatal(http.ListenAndServe(":8123", nil))
}

func encodeParams(params map[string]string) string {
	var parts []string
	for key, value := range params {
		parts = append(parts, fmt.Sprintf("%s=%s", key, value))
	}
	return strings.Join(parts, "&")
}
